// Generic execution of the existing immutable-pair bytecode. No proof callbacks.
#include <CommonCrypto/CommonDigest.h>
#include <array>
#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <sys/resource.h>
#include <unordered_map>
#include <vector>
using U=uint32_t;using Q=uint64_t;
U read(std::istream&f){U x;f.read((char*)&x,4);if(!f)throw std::runtime_error("truncated binary");return x;}
const char* names[]={"const","move","cons","head","tail","pair","atom","succ","not","branch","jump","call","return"};
struct Instruction{U op;std::vector<U>a;};struct Function{U arity,registers;std::vector<Instruction>code;};
struct Frame{U fn,pc,destination;std::vector<U>registers;};
int main(int argc,char**argv){
 if(argc!=7)return 2;auto before=std::chrono::steady_clock::now();CC_SHA256_CTX digest;CC_SHA256_Init(&digest);
 Q steps=0,limit=std::stoull(argv[4]),heaplimit=std::stoull(argv[5]),peak=0;std::string status="unknown_step_budget";U value=256;
 try{
  std::ifstream code(argv[1],std::ios::binary),input(argv[2],std::ios::binary);if(read(code)!=0x47545231||read(input)!=0x47544931)throw std::runtime_error("binary header");
  std::vector<U> constants(read(code));for(U&v:constants)v=read(code);std::vector<Function>functions(read(code));
  for(auto&f:functions){f.arity=read(code);f.registers=read(code);f.code.resize(read(code));for(auto&ins:f.code){ins.op=read(code);ins.a.resize(read(code));for(U&v:ins.a)v=read(code);}}
  U root=read(input),n=read(input);std::vector<std::array<U,2>>heap;heap.reserve(n+4096);std::unordered_map<Q,U>index;
  for(U i=0;i<n;i++){U a=read(input),b=read(input);if(a>=257+i||b>=257+i||index.count((Q(a)<<32)|b))throw std::runtime_error("canonical input heap");index[(Q(a)<<32)|b]=257+i;heap.push_back({a,b});}
  if(code.peek()!=std::char_traits<char>::eof()||input.peek()!=std::char_traits<char>::eof()||root>=257+n||functions.empty())throw std::runtime_error("binary frame");
  U fn=0,pc=0;std::vector<U>regs(functions.at(0).registers,256);regs.at(0)=root;std::vector<Frame>frames;std::vector<Q>profile(functions.size());
  auto cons=[&](U a,U b){if(a>=257+heap.size()||b>=257+heap.size())throw std::runtime_error("cons child");Q key=(Q(a)<<32)|b;auto it=index.find(key);if(it!=index.end())return it->second;if(heap.size()>=heaplimit)throw std::length_error("heap budget");U id=257+heap.size();index[key]=id;heap.push_back({a,b});return id;};
  for(;steps<limit;){const auto ins=functions.at(fn).code.at(pc);U oldfn=fn,oldpc=pc++;const auto&a=ins.a;U out=256;bool has=true,call=false,done=false;
   std::vector<U>arguments;
   try{
    switch(ins.op){
     case 0:regs.at(a.at(0))=out=constants.at(a.at(1));break;
     case 1:regs.at(a.at(0))=out=regs.at(a.at(1));break;
     case 2:regs.at(a.at(0))=out=cons(regs.at(a.at(1)),regs.at(a.at(2)));break;
     case 3:case 4:{U id=regs.at(a.at(1));if(id<257)throw std::runtime_error("pair required");regs.at(a.at(0))=out=heap.at(id-257).at(ins.op-3);break;}
     case 5:regs.at(a.at(0))=out=regs.at(a.at(1))>256;break;
     case 6:regs.at(a.at(0))=out=(regs.at(a.at(1))<=256&&regs.at(a.at(2))<=256&&regs.at(a.at(1))==regs.at(a.at(2)));break;
     case 7:{U v=regs.at(a.at(1));if(v>=255)throw std::runtime_error("byte successor");regs.at(a.at(0))=out=v+1;break;}
     case 8:{U v=regs.at(a.at(1));if(v>1)throw std::runtime_error("Boolean required");regs.at(a.at(0))=out=1-v;break;}
     case 9:out=regs.at(a.at(0));if(out>1)throw std::runtime_error("Boolean required");pc=a.at(1+out);break;
     case 10:pc=a.at(0);has=false;break;
     case 11:{U target=a.at(1),argc=a.at(2);if(argc!=functions.at(target).arity||a.size()!=3+argc)throw std::runtime_error("call arity");for(U j=0;j<argc;j++)arguments.push_back(regs.at(a.at(3+j)));frames.push_back({fn,pc,a.at(0),std::move(regs)});fn=target;pc=0;regs=arguments;regs.resize(functions.at(fn).registers,256);profile.at(fn)++;call=true;break;}
     case 12:out=regs.at(a.at(0));if(frames.empty()){value=out;status=out==1?"accepted":"rejected";done=true;}else{auto f=std::move(frames.back());frames.pop_back();fn=f.fn;pc=f.pc;regs=std::move(f.registers);regs.at(f.destination)=out;}break;
     default:throw std::runtime_error("opcode");
    }
   }catch(const std::length_error&){status="unknown_heap_budget";break;}catch(const std::exception&){status="rejected";steps++;break;}
   std::string event="["+std::to_string(oldfn)+","+std::to_string(oldpc)+",\""+names[ins.op]+"\"";
   if(call){event+=",[";for(size_t j=0;j<arguments.size();j++){if(j)event+=',';event+=std::to_string(arguments[j]);}event+=']';}else if(has)event+=","+std::to_string(out);
   event+="]\n";CC_SHA256_Update(&digest,event.data(),event.size());steps++;
   if(done)break;peak=std::max<Q>(peak,frames.size());
  }
  std::ofstream output(argv[3],std::ios::binary);auto put=[&](U v){output.write((char*)&v,4);};put(0x47544f31);put(value);put(heap.size());for(auto p:heap){put(p[0]);put(p[1]);}
  std::ofstream counts(argv[6]);counts<<'[';for(size_t i=0;i<profile.size();i++){if(i)counts<<',';counts<<profile[i];}counts<<']';
  unsigned char hash[32];CC_SHA256_Final(hash,&digest);std::ostringstream hex;hex<<std::hex;for(auto b:hash){hex.width(2);hex.fill('0');hex<<unsigned(b);}struct rusage usage{};getrusage(RUSAGE_SELF,&usage);
  std::cout<<"{\"status\":\""<<status<<"\",\"steps\":"<<steps<<",\"event_sha256\":\""<<hex.str()<<"\",\"peak_frames\":"<<peak<<",\"heap_nodes\":"<<heap.size()<<",\"value\":"<<value<<",\"peak_native_memory_bytes\":"<<usage.ru_maxrss<<",\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-before).count()<<"}\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
