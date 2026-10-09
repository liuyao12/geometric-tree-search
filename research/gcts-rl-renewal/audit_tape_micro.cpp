// Independent selected-tape interpreter. Reads only an explicit symbol table.
// No imports/calls into the compiler, literal runner, heap or logical checker.
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
#include <chrono>
using U=uint32_t;using Q=uint64_t;
U read(std::istream&f){U v;f.read(reinterpret_cast<char*>(&v),4);if(!f)throw std::runtime_error("short input");return v;}
void write(std::ostream&f,U v){f.write(reinterpret_cast<char*>(&v),4);}
struct Op{bool valid=false;U next=0,symbol=0,direction=1;};
struct Row{U tape;std::vector<Op> action;};
int main(int argc,char**argv){try{
 if(argc!=5)throw std::runtime_error("microcode input output limit");
 std::ifstream code(argv[1],std::ios::binary),input(argv[2],std::ios::binary);
 if(read(code)!=0x47544d32)throw std::runtime_error("micro magic");
 U count=read(code),state=read(code),accepted=read(code),rejected=read(code),space=read(code);
 std::vector<Row> rows(count);
 for(Row&r:rows){r.tape=read(code);r.action.resize(7);U n=read(code);for(U j=0;j<n;j++){U a=read(code),q=read(code),w=read(code),d=read(code);if(a>=7||w>=7||q>=count||d>2)throw std::runtime_error("bad micro action");r.action[a]={true,q,w,d};}}
 if(read(input)!=0x47544d33)throw std::runtime_error("micro input magic");
 U nt=read(input);std::vector<std::vector<U>> tape(nt);std::vector<int64_t> cursor(nt),base(nt);int64_t offset=1;
 for(U i=0;i<nt;i++){U n=read(input);cursor[i]=read(input);base[i]=offset+1;offset+=n+2;tape[i].resize(n);for(U&a:tape[i]){a=read(input);if(a>=7)throw std::runtime_error("bad symbol");}}
 Q limit=std::stoull(argv[4]),steps=0,physical=0,hash=14695981039346656037ULL;int64_t oldhead=0;
 auto start=std::chrono::steady_clock::now();
 while(state!=accepted&&state!=rejected&&state!=space&&steps<limit){
  Row&r=rows[state];U t=r.tape;if(t>=nt||cursor[t]<0||cursor[t]>=int64_t(tape[t].size())){state=space;break;}
  U a=tape[t][cursor[t]];Op action=r.action[a];if(!action.valid){state=rejected;break;}
  int64_t marker=base[t]+cursor[t];physical+=oldhead+marker+2+(action.direction!=1);
  Q event[]={state,t,Q(cursor[t]),a,action.next,action.symbol,action.direction};for(Q v:event)hash=1099511628211ULL*(hash^v);
  tape[t][cursor[t]]=action.symbol;cursor[t]+=int(action.direction)-1;oldhead=marker+int(action.direction)-1;state=action.next;steps++;
  if(cursor[t]<0||cursor[t]>=int64_t(tape[t].size())){state=space;break;}
 }
 std::ofstream out(argv[3],std::ios::binary);write(out,0x47544d34);write(out,state);write(out,nt);
 for(U t=0;t<nt;t++){write(out,U(cursor[t]));write(out,tape[t].size());for(U a:tape[t])write(out,a);}
 double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
 std::cout<<"{\"status\":\""<<(state==accepted?"accepted":state==rejected?"rejected":state==space?"unknown_space_budget":"unknown_step_budget")
 <<"\",\"micro_steps\":"<<steps<<",\"physical_steps\":"<<physical<<",\"micro_fnv64\":\""<<hash<<"\",\"seconds\":"<<seconds<<"}\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
