// Modified Glucose runner; use with glucose-anchor.patch and the upstream MIT-licensed solver.
#include "glucose30/core/Solver.h"
#include <fstream>
#include <iostream>
#include <string>
#include <cstdio>
#include <chrono>
#include <thread>
#include <atomic>
#include <map>
#include <array>
#include <vector>
static std::vector<std::array<int,4>> tileGeometry;static std::map<std::array<int,4>,int> tileAt;
int gcts_anchor_candidate(int v){if(v<=0||v>=(int)tileGeometry.size())std::abort();auto t=tileGeometry[v];std::array<int,4> anchorAtom={t[0],-t[1],-t[2],-t[3]};std::array<int,4> candidate={anchorAtom[0],0-anchorAtom[1],0-anchorAtom[2],0-anchorAtom[3]};return tileAt.at(candidate);}
int gcts_symmetry_candidate(int v,int g){auto t=tileGeometry[v];int perm[3]={g<8?0:1,g<8?1:0,2},normals[3]={2,1,0};std::array<int,4> u;int normal=0;for(int i=0;i<3;i++){if(perm[i]==normals[t[0]])normal=i;u[i+1]=((g%8)&(1<<i)?-1:1)*t[perm[i]+1];}u[0]=2-normal;return tileAt.at(u);}
static Glucose30::Solver* instance=nullptr;static FILE* marks=nullptr;static uint64_t learned=0,atoms=0;static auto begun=std::chrono::steady_clock::now();
void gcts_trace(int op,int a,int b){if(op==4&&instance&&instance->conflicts%50000==0)std::cerr<<"{\"conflicts\":"<<instance->conflicts<<",\"learnedPatterns\":"<<learned<<",\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-begun).count()<<"}\n";}
void gcts_learn(const Glucose30::vec<Glucose30::Lit>& clause){learned++;atoms+=clause.size();if(marks){uint32_t n=clause.size();fwrite(&n,4,1,marks);for(int i=0;i<clause.size();i++){uint32_t v=Glucose30::var(clause[i]);fwrite(&v,4,1,marks);}}}
void gcts_orbit_record(const Glucose30::vec<Glucose30::Lit>& c){gcts_learn(c);}
int main(int argc,char**argv){if(argc<7){std::cerr<<"CNF PROOF PATTERN_BINARY_OR_DASH SECONDS negative|geometry|symmetry PLACEMENTS required\n";return 2;}std::ifstream in(argv[1]);Glucose30::Solver solver;instance=&solver;solver.gctsGeometric=argc>5&&(std::string(argv[5])=="geometry"||std::string(argv[5])=="symmetry");solver.gctsSymmetry=argc>5&&std::string(argv[5])=="symmetry";
std::ifstream geometry(argv[6]);if(!geometry)return 2;tileGeometry.push_back({0,0,0,0});int oi,x,y,z;while(geometry>>oi>>x>>y>>z){std::array<int,4> t={oi,x,y,z};tileAt[t]=tileGeometry.size();tileGeometry.push_back(t);}
std::string tok;Glucose30::vec<Glucose30::Lit> clause;
while(in>>tok){if(tok=="c"||tok=="p"){std::getline(in,tok);continue;}int n=std::stoi(tok);if(n){while(solver.nVars()<=std::abs(n))solver.newVar(false,solver.nVars()!=0);clause.push(Glucose30::mkLit(std::abs(n),n<0));}else{if(!solver.addClause(clause))return 3;clause.clear();}}
solver.certifiedOutput=fopen(argv[2],"wb");solver.certifiedUNSAT=true;marks=std::string(argv[3])=="-"?nullptr:fopen(argv[3],"wb");std::atomic<bool> done(false);double seconds=std::stod(argv[4]);begun=std::chrono::steady_clock::now();std::thread timer([&](){while(!done){std::this_thread::sleep_for(std::chrono::milliseconds(100));if(std::chrono::duration<double>(std::chrono::steady_clock::now()-begun).count()>seconds){solver.interrupt();break;}}});Glucose30::vec<Glucose30::Lit> assumptions;auto answer=solver.solveLimited(assumptions);done=true;timer.join();fflush(solver.certifiedOutput);if(marks)fclose(marks);marks=nullptr;
std::cout<<"{\"status\":\""<<(answer==g3l_False?"UNSAT":answer==g3l_True?"SAT":"unknown")<<"\",\"conflicts\":"<<solver.conflicts<<",\"decisions\":"<<solver.decisions<<",\"learnedPatterns\":"<<learned<<",\"atoms\":"<<atoms<<",\"geometricUnits\":"<<solver.geometricUnits<<",\"geometricConflicts\":"<<solver.geometricConflicts<<",\"geometricTouches\":"<<solver.geometricTouches<<",\"geometricOrbitPatterns\":"<<solver.geometricOrbitPatterns<<",\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-begun).count()<<",\"selected\":[";bool comma=false;if(answer==g3l_True)for(int v=1;v<solver.model.size();v++)if(solver.model[v]==g3l_True){if(comma)std::cout<<",";std::cout<<v;comma=true;}std::cout<<"]}\n";
}
