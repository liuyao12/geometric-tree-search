// Link with the observationally instrumented PySAT Glucose 3.0 sources.
// Binary records are three little-endian int32 values: operation, a, b.
// 1 positive tile enqueue; 2 undo; 3 decision (signed literal, old level);
// 4 conflict (level, clause length); 5 backjump (new level); 6 search/restart;
// 7 terminal (0=UNSAT,1=SAT). All decisions, including auxiliary ones, remain.
#include "glucose30/core/Solver.h"
#include <fstream>
#include <iostream>
#include <string>
#include <cstdint>
#include <cstdio>
#include <chrono>
static FILE *trace_file = nullptr;
void gcts_trace(int op, int a, int b) {
    if (!trace_file) return;
    int32_t r[3] = {op,a,b};
    if (fwrite(r,sizeof(int32_t),3,trace_file)!=3) std::abort();
}
int main(int argc,char **argv) {
    if(argc!=4) { std::cerr<<"CNF TRACE PROOF required\n"; return 2; }
    std::ifstream input(argv[1]); if(!input) return 2;
    Glucose30::Solver solver;
    std::string token; Glucose30::vec<Glucose30::Lit> clause;
    while(input>>token) {
        if(token=="c"||token=="p") {std::getline(input,token);continue;}
        int lit=std::stoi(token);
        if(lit) {
            // Match PySAT's one-based variables, including its unused var 0.
            while(solver.nVars()<=std::abs(lit)) solver.newVar();
            clause.push(Glucose30::mkLit(std::abs(lit),lit<0));
        } else {if(!solver.addClause(clause)) return 3;clause.clear();}
    }
    solver.certifiedOutput=fopen(argv[3],"wb");
    if(!solver.certifiedOutput) return 2;
    solver.certifiedUNSAT=true;
    trace_file=fopen(argv[2],"wb"); if(!trace_file) return 2;
    const auto start=std::chrono::steady_clock::now();
    bool sat=solver.solve();
    gcts_trace(7,sat?1:0,0);
    fclose(trace_file);trace_file=nullptr;
    fflush(solver.certifiedOutput);
    std::cout<<"{\"status\":\""<<(sat?"SAT":"UNSAT")<<"\",\"decisions\":"<<solver.decisions
        <<",\"conflicts\":"<<solver.conflicts<<",\"searchStarts\":"<<solver.starts
        <<",\"propagations\":"<<solver.propagations<<",\"seconds\":"
        <<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<<"}\n";
}
