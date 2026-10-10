// Complete head-component counts/pages in the unchanged literal Wang palette.
// This process sees only the pinned transition table and integer symbol queries.
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
struct Action { uint32_t symbol,next,write,move; };
struct Row { uint32_t fallback,move; std::vector<Action> actions; };
class Table {
public:
 uint32_t A,Q,start,accept,reject,space; uint64_t defined=0; std::vector<Row> rows;
 explicit Table(const char* path) {
  std::ifstream in(path,std::ios::binary);if(!in)throw std::runtime_error("table file");
  auto word=[&](){uint32_t x;in.read(reinterpret_cast<char*>(&x),4);if(!in)throw std::runtime_error("truncated table");return x;};
  if(word()!=0x47544d31)throw std::runtime_error("magic");A=word();Q=word();start=word();accept=word();reject=word();space=word();
  if(!A||!Q||start>=Q||accept>=Q||reject>=Q||space>=Q)throw std::runtime_error("header");
  rows.reserve(Q);
  for(uint32_t q=0;q<Q;q++){
   Row r;r.fallback=word();r.move=word();word();word();uint32_t n=word();
   if(r.fallback>Q||r.move>2||n>A)throw std::runtime_error("row");
   for(uint32_t j=0;j<n;j++){
    Action a{word(),word(),word(),word()};word();
    if(a.symbol>=A||a.next>=Q||a.write>=A||a.move>2)throw std::runtime_error("action");
    r.actions.push_back(a);
   }
   std::sort(r.actions.begin(),r.actions.end(),[](auto a,auto b){return a.symbol<b.symbol;});
   for(size_t j=1;j<r.actions.size();j++)if(r.actions[j-1].symbol==r.actions[j].symbol)throw std::runtime_error("duplicate action");
   defined+=r.fallback?A:n;rows.push_back(std::move(r));
  }
  if(in.peek()!=EOF||rows[accept].fallback||!rows[accept].actions.empty())throw std::runtime_error("table length/accept");
 }
 bool member(uint64_t h,int role,int64_t north) const {
  if(h<A||h>=uint64_t(A)*(Q+1))throw std::runtime_error("head symbol");
  uint32_t q=(h-A)/A,s=(h-A)%A;
  if(q==accept)return role==0?(north== -1||(north< -1?s==uint64_t(-2-north):uint64_t(north)==h)):(north<0||north<A);
  const auto&r=rows[q];bool exists=r.fallback;uint32_t next=r.fallback?r.fallback-1:0,w=s,move=r.move;
  auto it=std::lower_bound(r.actions.begin(),r.actions.end(),s,[](auto a,auto b){return a.symbol<b;});
  if(it!=r.actions.end()&&it->symbol==s){exists=true;next=it->next;w=it->write;move=it->move;}
  if(role==0){if(!exists)return false;uint64_t output=move==1?uint64_t(A)+uint64_t(A)*next+w:w;return north== -1||(north< -1?w==uint64_t(-2-north):output==uint64_t(north));}
  if(north<0)return true;
  bool enters=exists&&move==(role==1?2:0);
  return north<A?!enters:(enters&&next==(uint64_t(north)-A)/A);
 }
};
int main(int argc,char**argv){
 try{
  if(argc!=2)throw std::runtime_error("usage");Table t(argv[1]);
  std::cout<<"READY "<<t.A<<' '<<t.Q<<' '<<t.start<<' '<<t.accept<<' '<<t.defined<<'\n'<<std::flush;
  std::string command;
  while(std::cin>>command){
   if(command=="quit")break;
   int role;int64_t north,n;uint64_t cursor,limit;std::cin>>role>>north>>n>>cursor>>limit;
   if(!std::cin||role<0||role>2||north>=int64_t(uint64_t(t.A)*(t.Q+1))||north< -1-int64_t(t.A)||n< -3||n>1000000||limit>4096)throw std::runtime_error("query");
   std::vector<uint64_t> ids;if(n>=0)for(int64_t i=0;i<n;i++){uint64_t v;std::cin>>v;ids.push_back(v);}
   uint64_t lo=t.A,hi=uint64_t(t.A)*(t.Q+1),stride=1;if(n==-2)std::cin>>lo>>hi;if(n==-3)std::cin>>lo>>hi>>stride;
   if(lo<t.A||hi>uint64_t(t.A)*(t.Q+1)||lo>hi||!stride)throw std::runtime_error("head interval");
   if(!std::cin||!std::is_sorted(ids.begin(),ids.end())||std::adjacent_find(ids.begin(),ids.end())!=ids.end())throw std::runtime_error("head set");
   if(command=="count"){
    uint64_t count=0;
    if(n<0&&north== -1&&(role!=0||(lo==t.A&&hi==uint64_t(t.A)*(t.Q+1)&&stride==1)))count=role==0?t.defined+t.A:(hi-lo+stride-1)/stride;
    else if(n<0)for(uint64_t h=lo;h<hi;h+=stride)count+=t.member(h,role,north);
    else for(auto h:ids)count+=t.member(h,role,north);
    std::cout<<"COUNT "<<count<<'\n'<<std::flush;
   }else if(command=="page"){
    std::vector<uint64_t> values;
    if(n<0){uint64_t first=lo+(cursor>lo?(cursor-lo+stride-1)/stride:0)*stride;for(uint64_t h=first;h<hi&&values.size()<limit;h+=stride)if(t.member(h,role,north))values.push_back(h);}
    else {for(auto h:ids)if(h>=cursor&&values.size()<limit&&t.member(h,role,north))values.push_back(h);}
    std::cout<<"PAGE "<<values.size();for(auto h:values)std::cout<<' '<<h;std::cout<<'\n'<<std::flush;
   }else throw std::runtime_error("command");
  }
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
