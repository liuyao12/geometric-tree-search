// Independent response algebra with arbitrary observed fragment roots.
// Observation node IDs do not affect validity or input application.
// Reads a grammar; never expands its root or
// executes the input computation. All interfaces, including unused nodes,
// are derived from finite symbol actions, copy sweeps and descending pairs.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>
#include <sstream>
#include <sys/resource.h>
using U=uint32_t;using Q=uint64_t;using I=int64_t;using Wide=__int128;
U get(std::istream&f){U x;f.read(reinterpret_cast<char*>(&x),4);if(!f)throw std::runtime_error("short binary");return x;}
Q large(std::istream&f){Q a=get(f),b=get(f);return a+(b<<32);}
void put(std::ostream&f,U v){f.write(reinterpret_cast<char*>(&v),4);}
Q memory(){rusage r{};getrusage(RUSAGE_SELF,&r);return Q(r.ru_maxrss);}
std::string decimal(Wide n){bool sign=n<0;if(sign)n=-n;std::string s;do{s.push_back('0'+n%10);n/=10;}while(n);if(sign)s.push_back('-');std::reverse(s.begin(),s.end());return s;}
struct Action{bool exists=false;U out=0,write=0,move=1;};struct Row{U t;std::array<Action,7> action;};
struct Run{I lo,hi;U v;};
struct Band{U t;I shift=0,lo=0,hi=0;Q coefficient=0;std::vector<Run> pre,writes;};
struct Response{U q,out,last;Q steps;Wide constant;std::vector<Band> bands;};
I displacement(const Response&r,U t){for(const Band&b:r.bands)if(b.t==t)return b.shift;return 0;}
void append(std::vector<Run>&r,I a,I b,I value){if(value<0)return;if(!r.empty()&&r.back().hi==a&&r.back().v==U(value))r.back().hi=b;else r.push_back({a,b,U(value)});}
Band merge(const Band&a,const Band&b,U last){
 Band c;c.t=a.t;c.shift=a.shift+b.shift;c.lo=std::min(a.lo,a.shift+b.lo);c.hi=std::max(a.hi,a.shift+b.hi);c.coefficient=a.coefficient+b.coefficient+(c.t==last);
 std::array<std::vector<Run>,4> lists{a.pre,a.writes,b.pre,b.writes};
 for(U j=2;j<4;j++)for(auto&r:lists[j]){r.lo+=a.shift;r.hi+=a.shift;}
 std::vector<I> cuts;for(auto&list:lists)for(auto&r:list){cuts.push_back(r.lo);cuts.push_back(r.hi);}
 std::sort(cuts.begin(),cuts.end());cuts.erase(std::unique(cuts.begin(),cuts.end()),cuts.end());std::array<size_t,4> pointers{};
 for(size_t i=1;i<cuts.size();i++){I lo=cuts[i-1],hi=cuts[i];std::array<I,4> val{-1,-1,-1,-1};
  for(U j=0;j<4;j++){auto&list=lists[j];while(pointers[j]<list.size()&&list[pointers[j]].hi<=lo)pointers[j]++;if(pointers[j]<list.size()&&list[pointers[j]].lo<=lo)val[j]=list[pointers[j]].v;}
  I pre=val[0],write=val[3]>=0?val[3]:val[1];
  if(val[2]>=0){if(val[1]>=0){if(!(val[2]&(I(1)<<val[1])))throw std::runtime_error("write/input conflict");}else{pre=pre<0?val[2]:pre&val[2];if(!pre)throw std::runtime_error("empty input intersection");}}
  if(write>=0&&pre==(I(1)<<write))write=-1;
  append(c.pre,lo,hi,pre);append(c.writes,lo,hi,write);
 }
 return c;
}
Response compose(const Response&a,const Response&b,Q limit){
 if(a.out!=b.q)throw std::runtime_error("state mismatch");
 if(a.steps>limit-b.steps)throw std::length_error("symbol budget");
 Response c{a.q,b.out,b.last,a.steps+b.steps,a.constant+b.constant+displacement(a,a.last),{}};
 for(const Band&v:b.bands)c.constant+=Wide(v.coefficient)*displacement(a,v.t);
 size_t x=0,y=0;
 while(x<a.bands.size()||y<b.bands.size()){
  U t=x==a.bands.size()?b.bands[y].t:y==b.bands.size()?a.bands[x].t:std::min(a.bands[x].t,b.bands[y].t);
  Band zero;zero.t=t;const Band&aa=x<a.bands.size()&&a.bands[x].t==t?a.bands[x]:zero;const Band&bb=y<b.bands.size()&&b.bands[y].t==t?b.bands[y]:zero;
  c.bands.push_back(merge(aa,bb,a.last));if(x<a.bands.size()&&a.bands[x].t==t)x++;if(y<b.bands.size()&&b.bands[y].t==t)y++;
 }
 return c;
}
void describe(std::ostream&out,const Response&r){
 out<<"{\"q\":"<<r.q<<",\"out\":"<<r.out<<",\"last\":"<<r.last<<",\"steps\":"<<r.steps<<",\"physical_constant\":\""<<decimal(r.constant)<<"\",\"bands\":[";
 bool first=true;for(const Band&b:r.bands){if(!first)out<<',';first=false;out<<"{\"tape\":"<<b.t<<",\"shift\":"<<b.shift<<",\"extent\":["<<b.lo<<','<<b.hi<<"],\"physical_coefficient\":"<<b.coefficient;
  for(auto pair:{std::make_pair("pre",&b.pre),std::make_pair("writes",&b.writes)}){out<<",\""<<pair.first<<"\":[";bool f=true;for(auto&run:*pair.second){if(!f)out<<',';f=false;out<<'['<<run.lo<<','<<run.hi<<','<<run.v<<']';}out<<']';}out<<'}';}out<<"]}";
}
int main(int argc,char**argv){auto begin=std::chrono::steady_clock::now();Q checked=0,totalintervals=0,peakintervals=0;try{
 if(argc!=9)throw std::runtime_error("microcode input grammar output symbol-limit interface-limit summary observed-node-ids");
 Q limit=std::stoull(argv[5]),worklimit=std::stoull(argv[6]);
 std::ifstream code(argv[1],std::ios::binary),input(argv[2],std::ios::binary),proof(argv[3],std::ios::binary);
 if(get(code)!=0x47544d32)throw std::runtime_error("code magic");
 U count=get(code),start=get(code),accept=get(code),reject=get(code),space=get(code);std::vector<Row> rows(count);
 for(Row&r:rows){r.t=get(code);U n=get(code);for(U i=0;i<n;i++){U a=get(code),q=get(code),w=get(code),d=get(code);if(a>=7||q>=count||w>=7||d>2||r.action[a].exists)throw std::runtime_error("bad row");r.action[a]={true,q,w,d};}}
 if(code.peek()!=std::char_traits<char>::eof())throw std::runtime_error("trailing code bytes");
 if(get(input)!=0x47544d33)throw std::runtime_error("input magic");U nt=get(input);std::vector<std::vector<U>> tape(nt);std::vector<I> heads(nt),base(nt);I offset=1;
 for(U t=0;t<nt;t++){U n=get(input);heads[t]=get(input);base[t]=offset+1;offset+=n+2;if(n<2||heads[t]<0||heads[t]>=n)throw std::runtime_error("band bounds");tape[t].resize(n);for(U&s:tape[t]){s=get(input);if(s>=7)throw std::runtime_error("input symbol");}if(tape[t][0]!=1)throw std::runtime_error("band origin");}
 if(input.peek()!=std::char_traits<char>::eof())throw std::runtime_error("trailing input bytes");
 if(get(proof)!=0x47444331)throw std::runtime_error("proof magic");U n=get(proof),root=get(proof),claimedstart=get(proof),claimedout=get(proof);Q claimedsteps=large(proof),claimedphysical=large(proof),claimedhead=large(proof);
 if(n>10000000)throw std::length_error("node budget");if(claimedsteps>limit)throw std::length_error("symbol budget");
 if(!n||root>=n||claimedstart!=start)throw std::runtime_error("root declaration");
 std::vector<std::array<U,4>> nodes(n);std::vector<Q> remaining(n),uses(n);
 for(U i=0;i<n;i++){for(U&v:nodes[i])v=get(proof);auto v=nodes[i];if(v[0]>2)throw std::runtime_error("node tag");if(v[0]==2){if(v[1]>=i||v[2]>=i||v[3])throw std::runtime_error("descending children");remaining[v[1]]++;remaining[v[2]]++;}}
 if(proof.peek()!=std::char_traits<char>::eof())throw std::runtime_error("trailing proof bytes");
 std::vector<bool> observed(n);std::vector<U> selected{root};for(size_t j=0;j<selected.size()&&selected.size()<31;j++){U id=selected[j];observed[id]=true;if(nodes[id][0]==2){selected.push_back(nodes[id][1]);selected.push_back(nodes[id][2]);}}
 for(U id:selected)observed[id]=true;
 std::ifstream requested(argv[8],std::ios::binary);U nrequested=get(requested);
 for(U j=0;j<nrequested;j++){U id=get(requested);if(id>=n)throw std::runtime_error("observed node range");observed[id]=true;}
 if(requested.peek()!=std::char_traits<char>::eof())throw std::runtime_error("observation trailing bytes");
 std::ostringstream observations;bool observationfirst=true;
 uses[root]=1;remaining[root]++;for(U i=n;i-->0;)if(nodes[i][0]==2)for(U child:{nodes[i][1],nodes[i][2]}){if(uses[i]>limit||uses[child]>limit-uses[i])throw std::length_error("expansion budget");uses[child]+=uses[i];}
 std::vector<std::shared_ptr<Response>> values(n);Q intervals=0,live=0,peak=0,expandedleaves=0;U depthmax=0;std::vector<U> depths(n);Q unused=0;
 for(U i=0;i<n;i++){
  auto node=nodes[i];Response r;
  if(node[0]==2){r=compose(*values[node[1]],*values[node[2]],limit);depths[i]=1+std::max(depths[node[1]],depths[node[2]]);}
  else{U q=node[1];if(q>=count||q==accept||q==reject||q==space||rows[q].t>=nt)throw std::runtime_error("leaf state");U t=rows[q].t;Band b;b.t=t;
   if(node[0]==0){U symbol=node[2];if(symbol>=7||node[3]||!rows[q].action[symbol].exists)throw std::runtime_error("leaf symbol");Action a=rows[q].action[symbol];I d=I(a.move)-1;
    b.shift=d;b.lo=std::min(I(0),d);b.hi=std::max(I(0),d);b.coefficient=1;b.pre.push_back({0,1,1U<<symbol});if(a.write!=symbol)b.writes.push_back({0,1,a.write});r={q,a.out,t,1,2+(d!=0),{std::move(b)}};
   }else{I d=I(node[2])-1;Q length=node[3];if((d!=-1&&d!=1)||!length||length>limit)throw std::runtime_error("sweep declaration");U mask=0;
    for(U s=0;s<7;s++){Action a=rows[q].action[s];if(a.exists&&a.out==q&&a.write==s&&I(a.move)-1==d)mask|=1U<<s;}if(!mask)throw std::runtime_error("sweep law");
    b.shift=d*I(length);b.lo=std::min(I(0),b.shift);b.hi=std::max(I(0),b.shift);b.coefficient=2*length-1;b.pre.push_back({d>0?0:1-I(length),d>0?I(length):1,mask});r={q,q,t,length,Wide(d)*length*(length-1)+3*Wide(length),{std::move(b)}};
   }
   expandedleaves+=uses[i];
  }
  Q size=0;for(auto&b:r.bands)size+=b.pre.size()+b.writes.size();if(size>worklimit-intervals)throw std::length_error("interface budget");intervals+=size;live+=size;peak=std::max(peak,live);depthmax=std::max(depthmax,depths[i]);checked=i+1;totalintervals=intervals;peakintervals=peak;
  values[i]=std::make_shared<Response>(std::move(r));if(!uses[i])unused++;
  if(observed[i]){const Response&v=*values[i];if(!observationfirst)observations<<',';observationfirst=false;observations<<"{\"node\":"<<i<<",\"children\":[";if(node[0]==2)observations<<node[1]<<','<<node[2];observations<<"],\"kind\":"<<node[0]<<",\"uses\":"<<uses[i]<<",\"intervals\":"<<size<<",\"depth\":"<<depths[i]<<",\"response\":";describe(observations,v);observations<<'}';}
  if(node[0]==2)for(U j:{node[1],node[2]}){if(!--remaining[j]){for(auto&b:values[j]->bands)live-=b.pre.size()+b.writes.size();values[j].reset();}}
  if(!remaining[i]){for(auto&b:values[i]->bands)live-=b.pre.size()+b.writes.size();values[i].reset();}
 }
 const Response&r=*values[root];if(r.q!=start||r.out!=claimedout||r.steps!=claimedsteps)throw std::runtime_error("derived root state/steps");
 Wide physical=r.constant;
 for(const Band&b:r.bands){physical+=Wide(b.coefficient)*(base[b.t]+heads[b.t]);if(heads[b.t]+b.lo<0||heads[b.t]+b.hi>=I(tape[b.t].size()))throw std::runtime_error("root frame");
  for(auto&run:b.pre)for(I p=run.lo;p<run.hi;p++)if(!(run.v&(1U<<tape[b.t][heads[b.t]+p])))throw std::runtime_error("root input");
 }
 for(const Band&b:r.bands){for(auto&run:b.writes)for(I p=run.lo;p<run.hi;p++)tape[b.t][heads[b.t]+p]=run.v;heads[b.t]+=b.shift;}
 if(physical<0||physical>Wide(UINT64_MAX)||Q(physical)!=claimedphysical||Q(base[r.last]+heads[r.last])!=claimedhead)throw std::runtime_error("derived physical boundary");
 std::ofstream output(argv[4],std::ios::binary);put(output,0x47544d34);put(output,r.out);put(output,nt);for(U t=0;t<nt;t++){put(output,U(heads[t]));put(output,tape[t].size());for(U a:tape[t])put(output,a);}
 std::ofstream summary(argv[7]);summary<<"{\"q\":"<<r.q<<",\"out\":"<<r.out<<",\"last\":"<<r.last<<",\"steps\":"<<r.steps<<",\"physical_constant\":\""<<decimal(r.constant)<<"\",\"observations\":["<<observations.str()<<"],\"bands\":[";
 bool first=true;for(const Band&b:r.bands){if(!first)summary<<',';first=false;summary<<"{\"tape\":"<<b.t<<",\"shift\":"<<b.shift<<",\"extent\":["<<b.lo<<','<<b.hi<<"],\"physical_coefficient\":"<<b.coefficient;
  for(auto pair:{std::make_pair("pre",&b.pre),std::make_pair("writes",&b.writes)}){summary<<",\""<<pair.first<<"\":[";bool f=true;for(auto&run:*pair.second){if(!f)summary<<',';f=false;summary<<'['<<run.lo<<','<<run.hi<<','<<run.v<<']';}summary<<']';}summary<<'}';}summary<<"]}\n";
 std::cout<<"{\"status\":\"checked_response\",\"result\":\""<<(r.out==accept?"accepted":r.out==reject?"rejected":r.out==space?"unknown_space_budget":"unknown_prefix")<<"\",\"nodes\":"<<n<<",\"micro_steps\":"<<r.steps<<",\"physical_steps\":"<<Q(physical)<<",\"expanded_leaves\":"<<expandedleaves<<",\"derived_intervals\":"<<intervals<<",\"peak_live_intervals\":"<<peak<<",\"unused_nodes_checked\":"<<unused<<",\"max_depth\":"<<depthmax<<",\"peak_native_memory_bytes\":"<<memory()<<",\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count()<<"}\n";
}catch(const std::length_error&e){std::cout<<"{\"status\":\"unknown_certificate_budget\",\"reason\":\""<<e.what()<<"\",\"checked_nodes\":"<<checked<<",\"derived_intervals\":"<<totalintervals<<",\"peak_live_intervals\":"<<peakintervals<<",\"peak_native_memory_bytes\":"<<memory()<<",\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count()<<"}\n";return 0;}catch(const std::bad_alloc&){std::cout<<"{\"status\":\"unknown_memory_budget\"}\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
