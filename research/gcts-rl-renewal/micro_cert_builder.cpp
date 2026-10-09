// Generic selected-symbol execution with an interned, descending response DAG.
// Leaves are symbol-table transitions or repeated identity moves; no proof,
// register, heap, syntax, inference or parser callbacks are present.
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <unordered_map>
#include <vector>
#include <sys/resource.h>
using U=uint32_t;using Q=uint64_t;using I=int64_t;
U read(std::istream&f){U v;f.read(reinterpret_cast<char*>(&v),4);if(!f)throw std::runtime_error("short binary");return v;}
void put(std::ostream&f,U v){f.write(reinterpret_cast<char*>(&v),4);}
void big(std::ostream&f,Q v){put(f,U(v));put(f,U(v>>32));}
Q memory(){rusage r{};getrusage(RUSAGE_SELF,&r);return Q(r.ru_maxrss);}
struct Op{bool valid=false;U q=0,w=0,d=1;};struct Row{U tape;std::array<Op,7> ops;};
using Node=std::array<U,4>;
struct Hash{size_t operator()(const Node&n)const{Q h=14695981039346656037ULL;for(U x:n)h=(h^x)*1099511628211ULL;return size_t(h);}};
int main(int argc,char**argv){try{
 if(argc!=8)throw std::runtime_error("code input grammar output step-limit node-limit grouping-cuts");
 std::ifstream code(argv[1],std::ios::binary),in(argv[2],std::ios::binary);
 if(read(code)!=0x47544d32)throw std::runtime_error("code magic");
 U count=read(code),state=read(code),start=state,accepted=read(code),rejected=read(code),space=read(code);
 std::vector<Row> rows(count);
 for(auto&r:rows){r.tape=read(code);U n=read(code);for(U i=0;i<n;i++){U a=read(code),q=read(code),w=read(code),d=read(code);if(a>=7||q>=count||w>=7||d>2||r.ops[a].valid)throw std::runtime_error("bad row");r.ops[a]={true,q,w,d};}}
 if(read(in)!=0x47544d33)throw std::runtime_error("input magic");
 U nt=read(in);std::vector<std::vector<U>> tape(nt);std::vector<I> heads(nt),base(nt);I offset=1;
 for(U t=0;t<nt;t++){U n=read(in);heads[t]=read(in);base[t]=offset+1;offset+=n+2;tape[t].resize(n);for(U&a:tape[t]){a=read(in);if(a>=7)throw std::runtime_error("input symbol");}}
 Q limit=std::stoull(argv[5]),maxnodes=std::stoull(argv[6]),steps=0,physical=0,tokens=0,phrases=0;I oldhead=0;
 std::vector<Node> nodes;std::unordered_map<Node,U,Hash> index;std::vector<std::pair<U,U>> forest,outer;bool budget=false;
 std::ifstream cuts(argv[7],std::ios::binary);std::vector<bool> cut(count);U nc=read(cuts);for(U i=0;i<nc;i++)cut.at(read(cuts))=true;
 auto add=[&](Node n){auto p=index.find(n);if(p!=index.end())return p->second;if(nodes.size()>=maxnodes){budget=true;throw std::runtime_error("node budget");}U id=nodes.size();nodes.push_back(n);index.emplace(n,id);return id;};
 auto push=[&](std::vector<std::pair<U,U>>&stack,U id){U level=0;while(!stack.empty()&&stack.back().first==level){id=add({2,stack.back().second,id,0});stack.pop_back();level++;}stack.emplace_back(level,id);};
 auto flush=[&](){U id=UINT32_MAX;for(auto&item:forest)id=id==UINT32_MAX?item.second:add({2,id,item.second,0});forest.clear();if(id!=UINT32_MAX){push(outer,id);phrases++;}};
 auto emit=[&](Node n){push(forest,add(n));tokens++;};
 auto started=std::chrono::steady_clock::now();
 try{
 while(state!=accepted&&state!=rejected&&state!=space&&steps<limit){
  if(cut[state])flush();
  const Row&r=rows.at(state);U t=r.tape;if(t>=nt||heads[t]<0||heads[t]>=I(tape[t].size())){state=space;break;}
  U a=tape[t][heads[t]];Op op=r.ops[a];if(!op.valid){state=rejected;break;}
  I move=I(op.d)-1,marker=base[t]+heads[t];Q n=0;
  if(op.q==state&&op.w==a&&move){U mask=0;for(U s=0;s<7;s++){Op v=r.ops[s];if(v.valid&&v.q==state&&v.w==s&&v.d==op.d)mask|=1U<<s;}
   while(steps+n<limit&&heads[t]+move*I(n+1)>=0&&heads[t]+move*I(n+1)<I(tape[t].size())&&(mask&(1U<<tape[t][heads[t]+move*I(n)])))n++;
  }
  if(n>1){emit({1,state,op.d,U(n)});physical+=Q(oldhead)+(2*n-1)*Q(marker)+Q(move*I(n*(n-1)))+3*n;heads[t]+=move*I(n);oldhead=base[t]+heads[t];steps+=n;}
  else{emit({0,state,a,0});physical+=Q(oldhead+marker+2+(move!=0));tape[t][heads[t]]=op.w;heads[t]+=move;oldhead=marker+move;state=op.q;steps++;if(heads[t]<0||heads[t]>=I(tape[t].size())){state=space;break;}}
 }
 }catch(const std::runtime_error&){if(!budget)throw;}
 U root=UINT32_MAX;
 if(!budget){try{flush();for(auto& item:outer)root=root==UINT32_MAX?item.second:add({2,root,item.second,0});}catch(const std::runtime_error&){if(!budget)throw;}}
 std::ofstream out(argv[4],std::ios::binary);put(out,0x47544d34);put(out,state);put(out,nt);
 for(U t=0;t<nt;t++){put(out,U(heads[t]));put(out,tape[t].size());for(U a:tape[t])put(out,a);}
 if(!budget){std::ofstream cert(argv[3],std::ios::binary);put(cert,0x47444331);put(cert,nodes.size());put(cert,root);put(cert,start);put(cert,state);big(cert,steps);big(cert,physical);big(cert,Q(oldhead));for(auto&node:nodes)for(U v:node)put(cert,v);}
 std::cout<<"{\"status\":\""<<(budget?"unknown_certificate_budget":state==accepted?"accepted":state==rejected?"rejected":state==space?"unknown_space_budget":"unknown_step_budget")<<"\",\"micro_steps\":"<<steps<<",\"physical_steps\":"<<physical<<",\"nodes\":"<<nodes.size()<<",\"tokens\":"<<tokens<<",\"phrases\":"<<phrases<<",\"root\":"<<root<<",\"peak_native_memory_bytes\":"<<memory()<<",\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count()<<"}\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
