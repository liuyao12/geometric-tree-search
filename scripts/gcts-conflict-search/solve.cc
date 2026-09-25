// Standalone finite point/candidate search with CDCL conflict learning.
// No Glucose/MiniSat code or solver library is linked. See README for scope.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <limits>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;

struct Clause { vector<int> lits; bool learned=false, deleted=false; int lbd=0; };
struct Point {
    int x,y,z,generation,seed,free=0,covered=0,enabled=0;
    vector<int> covers,triggers;
};
struct Solver {
    int n=0,base=0,head=0;
    vector<Clause> clauses;
    vector<vector<int>> watch,coverInc,triggerInc;
    vector<int> value,level,reason,trail,limits;
    vector<double> activity;
    vector<unsigned char> seen;
    vector<Point> points;
    // All active uncovered points are indexed by generation, degree, identity.
    set<pair<pair<int,int>,int>> frontier;
    double bump=1;
    long long decisions=0,conflicts=0,propagations=0,forced=0,restarts=0,backjumps=0,learned=0,deletions=0;
    long long graphUpdates=0;
    ofstream proof;
    bool audit=false;
    chrono::steady_clock::time_point begun;
    double seconds=0;
    int li(int lit) const {return 2*(abs(lit)-1)+(lit<0);}
    int val(int lit) const {return value[abs(lit)]*(lit>0?1:-1);}
    int depth() const {return int(limits.size());}
    double elapsed() const {return chrono::duration<double>(chrono::steady_clock::now()-begun).count();}
    auto key(int p) const {return make_pair(make_pair(points[p].generation,points[p].free),p);}
    bool active(int p) const {return (points[p].seed||points[p].enabled)&&!points[p].covered;}
    void erasePoint(int p){if(active(p))frontier.erase(key(p));}
    void insertPoint(int p){if(active(p))frontier.insert(key(p));}
    void graphChange(int v,int sign,int delta){
        for(int p:coverInc[v]){
            erasePoint(p);points[p].free-=delta;
            if(sign>0)points[p].covered+=delta;
            insertPoint(p);graphUpdates++;
        }
        if(sign>0)for(int p:triggerInc[v]){
            erasePoint(p);points[p].enabled+=delta;insertPoint(p);graphUpdates++;
        }
    }
    void checkGraph(){
        if(!audit)return;
        set<pair<pair<int,int>,int>> expected;
        for(int i=0;i<(int)points.size();i++){
            auto& p=points[i];int f=0,c=0,e=0;
            for(int v:p.covers){f+=value[v]==0;c+=value[v]>0;}
            for(int v:p.triggers)e+=value[v]>0;
            if(f!=p.free||c!=p.covered||e!=p.enabled)throw runtime_error("incremental graph mismatch");
            if((p.seed||e)&&!c)expected.insert({{p.generation,f},i});
        }
        if(expected!=frontier)throw runtime_error("frontier rollback mismatch");
    }
    bool enqueue(int lit,int why){
        if(val(lit))return val(lit)>0;
        int v=abs(lit);value[v]=lit>0?1:-1;level[v]=depth();reason[v]=why;
        trail.push_back(lit);graphChange(v,value[v],1);return true;
    }
    void undo(int target){
        if(depth()<=target)return;
        int cut=limits[target];
        for(int i=(int)trail.size()-1;i>=cut;i--){
            int v=abs(trail[i]);graphChange(v,value[v],-1);value[v]=0;reason[v]=-1;level[v]=0;
        }
        trail.resize(cut);limits.resize(target);head=min(head,cut);checkGraph();
    }
    void emit(const vector<int>& c,bool deletion=false){
        if(deletion)proof<<"d ";for(int l:c)proof<<l<<' ';proof<<"0\n";
    }
    int add(vector<int> c,bool learnedClause=false,int lbd=0){
        int id=clauses.size();clauses.push_back({std::move(c),learnedClause,false,lbd});
        auto& ls=clauses[id].lits;
        if(learnedClause){emit(ls);learned++;}
        if(ls.size()>1){watch[li(ls[0])].push_back(id);watch[li(ls[1])].push_back(id);}
        return id;
    }
    // Two watched literals preserve complete unit propagation; explanations
    // are the original coverage/overlap clauses or proved learned constraints.
    int propagate(){
        while(head<(int)trail.size()){
            int falseLit=-trail[head++];propagations++;
            auto& ws=watch[li(falseLit)];size_t out=0;
            for(size_t j=0;j<ws.size();j++){
                int id=ws[j];auto& c=clauses[id];if(c.deleted)continue;
                auto& a=c.lits;
                if(a[0]==falseLit)swap(a[0],a[1]);
                if(a[1]!=falseLit)throw runtime_error("bad watcher");
                if(val(a[0])>0){ws[out++]=id;continue;}
                size_t k=2;while(k<a.size()&&val(a[k])<0)k++;
                if(k<a.size()){
                    swap(a[1],a[k]);watch[li(a[1])].push_back(id);continue;
                }
                ws[out++]=id;
                if(val(a[0])<0){
                    while(++j<ws.size())ws[out++]=ws[j];ws.resize(out);return id;
                }
                if(a[0]>0)forced++;
                enqueue(a[0],id);
            }
            ws.resize(out);
        }
        return -1;
    }
    void bumpVar(int v){
        activity[v]+=bump;
        if(activity[v]>1e100){for(auto& a:activity)a*=1e-100;bump*=1e-100;}
    }
    vector<int> analyze(int conflict,int& back,int& lbd){
        vector<int> out(1),touched;int pending=0,pivot=0,idx=trail.size()-1;
        do {
            if(conflict<0)throw runtime_error("missing implication reason");
            for(int l:clauses[conflict].lits){
                int v=abs(l);if(v==abs(pivot)||seen[v]||level[v]==0)continue;
                seen[v]=1;touched.push_back(v);bumpVar(v);
                if(level[v]==depth())pending++;else out.push_back(l);
            }
            while(idx>=0&&!seen[abs(trail[idx])])idx--;
            if(idx<0)throw runtime_error("conflict has no current-level literal");
            pivot=trail[idx--];seen[abs(pivot)]=0;pending--;
            conflict=reason[abs(pivot)];
        }while(pending);
        out[0]=-pivot;
        for(int v:touched)seen[v]=0;
        back=0;int best=1;set<int> levels;
        for(size_t i=0;i<out.size();i++){
            int d=level[abs(out[i])];levels.insert(d);
            if(i&&d>back){back=d;best=i;}
        }
        if(out.size()>1)swap(out[1],out[best]);
        lbd=levels.size();bump/=0.95;return out;
    }
    void reduce(){
        vector<unsigned char> locked(clauses.size());
        for(int l:trail)if(reason[abs(l)]>=0)locked[reason[abs(l)]]=1;
        vector<int> candidates;
        for(int i=base;i<(int)clauses.size();i++){
            auto& c=clauses[i];if(!c.deleted&&!locked[i]&&c.lits.size()>2&&c.lbd>2)candidates.push_back(i);
        }
        sort(candidates.begin(),candidates.end(),[&](int a,int b){
            if(clauses[a].lbd!=clauses[b].lbd)return clauses[a].lbd>clauses[b].lbd;
            return a<b;
        });
        for(size_t i=0;i<candidates.size()/2;i++){
            auto& c=clauses[candidates[i]];emit(c.lits,true);c.deleted=true;deletions++;
            vector<int>().swap(c.lits);
        }
    }
    void load(const string& cnf,const string& model){
        ifstream f(cnf);if(!f)throw runtime_error("cannot open CNF");
        string token;int count=0;
        while(f>>token){if(token=="c"){getline(f,token);continue;}
            if(token=="p"){f>>token>>n>>count;break;}}
        if(n<=0)throw runtime_error("invalid DIMACS header");
        value.assign(n+1,0);level=value;reason.assign(n+1,-1);seen.assign(n+1,0);activity.assign(n+1,0);
        watch.resize(2*n);coverInc.resize(n+1);triggerInc.resize(n+1);
        for(int i=0;i<count;i++){vector<int> c;int l;
            while(f>>l&&l){if(abs(l)>n)throw runtime_error("bad variable");c.push_back(l);}
            if(!f)throw runtime_error("truncated CNF");add(std::move(c));}
        base=clauses.size();
        ifstream g(model);int pn,np;if(!(g>>pn>>np)||pn!=n)throw runtime_error("invalid point model");
        for(int i=0;i<np;i++){
            Point p;int nc,nt;g>>p.x>>p.y>>p.z>>p.generation>>p.seed>>nc>>nt;
            for(int j=0;j<nc;j++){int v;g>>v;if(v<1||v>n)throw runtime_error("bad candidate");p.covers.push_back(v);coverInc[v].push_back(i);}
            for(int j=0;j<nt;j++){int v;g>>v;if(v<1||v>n)throw runtime_error("bad trigger");p.triggers.push_back(v);triggerInc[v].push_back(i);}
            if(!g)throw runtime_error("truncated point model");p.free=nc;points.push_back(std::move(p));insertPoint(i);
        }
    }
    int choose(){
        checkGraph();
        // Global zero/one checks precede generation ordering, even in models
        // with several declared generations. Propagation must already close them.
        for(const auto& entry:frontier)if(entry.first.second<=1)throw runtime_error("unpropagated dead/forced point");
        if(frontier.empty())return 0;
        const auto& p=points[frontier.begin()->second];
        int best=0;for(int v:p.covers)if(!value[v]&&(!best||activity[v]>activity[best]))best=v;
        if(!best)throw runtime_error("empty branch domain");return best;
    }
    bool finalCheck(){
        // All unassigned placements are omitted in a finite witness.
        for(auto& c:clauses)if(!c.deleted){bool sat=false;
            for(int l:c.lits)if((l>0&&value[l]>0)||(l<0&&value[-l]<=0)){sat=true;break;}
            if(!sat)return false;}
        return true;
    }
    string solve(){
        begun=chrono::steady_clock::now();
        for(int i=0;i<base;i++){
            if(clauses[i].lits.empty()){emit({});return "UNSAT";}
            if(clauses[i].lits.size()==1&&!enqueue(clauses[i].lits[0],i)){emit({});return "UNSAT";}
        }
        long long restartAt=128,interval=128,reduceAt=4000;
        while(true){
            if(elapsed()>seconds)return "unknown";
            int conflict=propagate();
            if(conflict>=0){
                conflicts++;
                if(!depth()){emit({});return "UNSAT";}
                int back,lbd;auto c=analyze(conflict,back,lbd);
                if(back<depth()-1)backjumps++;
                undo(back);int id=add(std::move(c),true,lbd);enqueue(clauses[id].lits[0],id);
                if(conflicts%10000==0)cerr<<"{\"conflicts\":"<<conflicts<<",\"seconds\":"<<elapsed()<<"}\n";
            }else{
                if(conflicts>=restartAt){undo(0);restarts++;interval=min(8192LL,interval+interval/10);restartAt=conflicts+interval;continue;}
                if(conflicts>=reduceAt){reduce();reduceAt=conflicts+4000;}
                int v=choose();
                if(!v){if(!finalCheck())throw runtime_error("model fails formula");return "SAT";}
                limits.push_back(trail.size());decisions++;enqueue(v,-1);
            }
        }
    }
};
int main(int argc,char**argv){try{
    if(argc<5)throw runtime_error("usage: gcts-conflict INPUT.cnf INPUT.points OUTPUT.drup SECONDS [--audit]");
    Solver s;s.seconds=stod(argv[4]);s.audit=argc>5&&string(argv[5])=="--audit";
    s.proof.open(argv[3]);if(!s.proof)throw runtime_error("cannot open proof");
    auto start=chrono::steady_clock::now();s.load(argv[1],argv[2]);
    double load=chrono::duration<double>(chrono::steady_clock::now()-start).count();
    string status=s.solve();s.proof.close();
    cout<<"{\"status\":\""<<status<<"\",\"seconds\":"<<s.elapsed()<<",\"loadSeconds\":"<<load
        <<",\"decisions\":"<<s.decisions<<",\"conflicts\":"<<s.conflicts<<",\"propagations\":"<<s.propagations
        <<",\"forcedPlacements\":"<<s.forced<<",\"backjumps\":"<<s.backjumps<<",\"restarts\":"<<s.restarts
        <<",\"learnedConstraints\":"<<s.learned<<",\"deletedConstraints\":"<<s.deletions<<",\"graphUpdates\":"<<s.graphUpdates<<",\"selected\":[";
    bool comma=false;if(status=="SAT")for(int v=1;v<=s.n;v++)if(s.value[v]>0){if(comma)cout<<',';cout<<v;comma=true;}
    cout<<"]}\n";return 0;
}catch(const exception& e){cerr<<e.what()<<'\n';return 1;}}
