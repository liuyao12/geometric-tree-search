// Persistent table transport; every query resets the whole explicit machine.
// No formula, proof rule, target, heap, parser or search callback is present.
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include <sys/resource.h>
using U=uint32_t;using Q=uint64_t;using I=int64_t;
U get(std::istream&f){U x;f.read(reinterpret_cast<char*>(&x),4);if(!f)throw std::runtime_error("short input");return x;}
void put(std::ostream&f,U x){f.write(reinterpret_cast<char*>(&x),4);}
struct Op{bool valid=false;U out=0,write=0,direction=1;};
struct Row{U tape;std::array<Op,7> actions;};
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("fixed micro table");std::ifstream code(argv[1],std::ios::binary);if(get(code)!=0x47544d32)throw std::runtime_error("table magic");
 U count=get(code),start=get(code),accept=get(code),reject=get(code),space=get(code);std::vector<Row> rows(count);
 for(auto&r:rows){r.tape=get(code);U n=get(code);for(U j=0;j<n;j++){U a=get(code),q=get(code),w=get(code),d=get(code);if(a>=7||q>=count||w>=7||d>2||r.actions[a].valid)throw std::runtime_error("bad transition");r.actions[a]={true,q,w,d};}}
 if(code.peek()!=std::char_traits<char>::eof())throw std::runtime_error("trailing table");std::cout<<"READY "<<count<<' '<<start<<' '<<accept<<' '<<reject<<' '<<space<<std::endl;
 std::string input,output;Q limit;
 while(std::cin>>input){if(input=="quit")break;if(!(std::cin>>output>>limit))throw std::runtime_error("query protocol");auto began=std::chrono::steady_clock::now();std::ifstream f(input,std::ios::binary);if(get(f)!=0x47544d33)throw std::runtime_error("input magic");
  U nt=get(f);std::vector<std::vector<U>> tapes(nt);std::vector<I> heads(nt),base(nt);I offset=1;
  for(U t=0;t<nt;t++){U n=get(f);heads[t]=get(f);base[t]=offset+1;offset+=n+2;if(!n||heads[t]>=n)throw std::runtime_error("initial frame");tapes[t].resize(n);for(U&s:tapes[t]){s=get(f);if(s>=7)throw std::runtime_error("input symbol");}}
  if(f.peek()!=std::char_traits<char>::eof())throw std::runtime_error("trailing input");U q=start;I oldhead=0;Q steps=0,physical=0,hash=14695981039346656037ULL;
  while(q!=accept&&q!=reject&&q!=space&&steps<limit){const Row&r=rows[q];U t=r.tape;if(t>=nt||heads[t]<0||heads[t]>=I(tapes[t].size())){q=space;break;}U s=tapes[t][heads[t]];const Op&o=r.actions[s];if(!o.valid){q=reject;break;}
   I marker=base[t]+heads[t];physical+=oldhead+marker+2+(o.direction!=1);Q event[]={q,t,Q(heads[t]),s,o.out,o.write,o.direction};for(Q v:event)hash=(hash^v)*1099511628211ULL;tapes[t][heads[t]]=o.write;heads[t]+=I(o.direction)-1;oldhead=marker+I(o.direction)-1;q=o.out;steps++;if(heads[t]<0||heads[t]>=I(tapes[t].size())){q=space;break;}}
  std::ofstream out(output,std::ios::binary);put(out,0x47544d34);put(out,q);put(out,nt);for(U t=0;t<nt;t++){put(out,U(heads[t]));put(out,tapes[t].size());for(U s:tapes[t])put(out,s);}out.close();rusage rss{};getrusage(RUSAGE_SELF,&rss);
  std::cout<<"{\"status\":\""<<(q==accept?"accepted":q==reject?"rejected":q==space?"unknown_space_budget":"unknown_step_budget")<<"\",\"state\":"<<q<<",\"start\":"<<start<<",\"micro_steps\":"<<steps<<",\"physical_steps\":"<<physical<<",\"micro_fnv64\":\""<<hash<<"\",\"physical_head\":"<<oldhead<<",\"peak_native_memory_bytes\":"<<rss.ru_maxrss<<",\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count()<<"}"<<std::endl;
 }
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
