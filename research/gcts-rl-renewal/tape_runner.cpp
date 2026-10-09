// Generic literal finite one-tape table runner. No heap/register/proof callbacks.
// Self-copy sweeps use exact symbol-occurrence indices. Their state and every
// skipped cell are unchanged; the full literal transition count is retained.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <vector>
using U=uint32_t;using Q=uint64_t;
U u(std::istream& f){U x;f.read(reinterpret_cast<char*>(&x),4);if(!f)throw std::runtime_error("truncated binary");return x;}
void put(std::ostream& f,U x){f.write(reinterpret_cast<char*>(&x),4);}
struct Action{U a,out,w,move,mout;};
struct Row{U def,dir,micro,tape;std::vector<Action> choices;int group=-1;};
int main(int argc,char**argv){try{
 if(argc!=5)throw std::runtime_error("machine input output limit");
 std::ifstream m(argv[1],std::ios::binary),in(argv[2],std::ios::binary);
 if(u(m)!=0x47544d31)throw std::runtime_error("machine magic");
 U alphabet=u(m),count=u(m),state=u(m),accept=u(m),reject=u(m),space=u(m);
 std::vector<Row> rows(count);std::map<std::vector<U>,int> groups;
 std::vector<std::vector<int>> membership(alphabet);
 for(U q=0;q<count;q++){
  Row&r=rows[q];r.def=u(m);r.dir=u(m);r.micro=u(m);r.tape=u(m);U n=u(m);
  for(U j=0;j<n;j++){Action a{u(m),u(m),u(m),u(m),u(m)};if(a.a>=alphabet||a.out>=count||a.w>=alphabet||a.move>2)throw std::runtime_error("bad action");r.choices.push_back(a);}
  if(r.def==q+1 && r.dir!=1){std::vector<U> syms;for(auto&a:r.choices)syms.push_back(a.a);std::sort(syms.begin(),syms.end());
   auto found=groups.find(syms);if(found==groups.end()){int id=groups.size();groups[syms]=id;for(U s:syms)membership[s].push_back(id);r.group=id;}else r.group=found->second;
  }
 }
 if(u(in)!=0x47544931)throw std::runtime_error("input magic");
 U nt=u(in);std::vector<U> base(nt);U offset=1;
 for(U i=0;i<nt;i++){base[i]=offset+1;offset+=u(in)+2;}
 U width=u(in);std::vector<U> tape(width);
 std::vector<std::set<int64_t>> positions(groups.size());
 for(U i=0;i<width;i++){tape[i]=u(in);if(tape[i]>=alphabet)throw std::runtime_error("bad tape symbol");for(int g:membership[tape[i]])positions[g].insert(i);}
 Q limit=std::stoull(argv[4]),steps=0,micro=0,digest=14695981039346656037ULL,sweeps=0,sweep_steps=0;int64_t head=0;
 auto started=std::chrono::steady_clock::now();
 while(state!=accept && state!=reject && state!=space && steps<limit){
  if(head<0||head>=width){state=space;break;}
  Row&r=rows[state];U symbol=tape[head];const Action*found=nullptr;
  for(auto&a:r.choices)if(a.a==symbol){found=&a;break;}
  if(!found && r.group>=0){
   auto& ps=positions[r.group];int64_t end=r.dir==2?int64_t(width):-1;
   if(r.dir==2){auto p=ps.upper_bound(head);if(p!=ps.end())end=*p;}
   else{auto p=ps.lower_bound(head);if(p!=ps.begin()){--p;end=*p;}}
   Q distance=uint64_t(end>head?end-head:head-end),n=std::min(distance,limit-steps);
   if(!n)throw std::runtime_error("zero sweep");
   head+=(r.dir==2?int64_t(n):-int64_t(n));steps+=n;sweep_steps+=n;sweeps++;continue;
  }
  if(!found){if(!r.def){state=reject;break;}state=r.def-1;head+=int(r.dir)-1;steps++;continue;}
  Action a=*found;
  if(r.micro && symbol>=9 && symbol<16){
   Q values[]={Q(r.micro-1),r.tape,Q(head-base.at(r.tape)),Q(symbol-9),a.mout,Q(a.w>=9?a.w-9:a.w-1),a.move};
   for(Q x:values)digest=(digest^x)*1099511628211ULL;micro++;
  }
  if(a.w!=symbol){for(int g:membership[symbol])positions[g].erase(head);for(int g:membership[a.w])positions[g].insert(head);tape[head]=a.w;}
  state=a.out;head+=int(a.move)-1;steps++;
 }
 double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
 std::ofstream out(argv[3],std::ios::binary);put(out,0x47544f31);put(out,state);put(out,U(head));put(out,width);for(U s:tape)put(out,s);
 std::cout<<"{\"status\":\""<<(state==accept?"accepted":state==reject?"rejected":state==space?"unknown_space_budget":"unknown_step_budget")
 <<"\",\"physical_steps\":"<<steps<<",\"micro_steps\":"<<micro<<",\"micro_fnv64\":\""<<digest
 <<"\",\"sweeps\":"<<sweeps<<",\"sweep_steps\":"<<sweep_steps<<",\"state\":"<<state<<",\"head\":"<<head<<",\"seconds\":"<<seconds<<"}\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
