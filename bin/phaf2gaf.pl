#!/usr/bin/perl
while(<>) {
    chomp;
    my @vals = split(/\t/,$_);
    my @nv = (
        $vals[0],
        $vals[1],
        $vals[1],
        "",
        $vals[2],
        $vals[17],
        "IMP",
        "",
        "Ph",
        "",
        "",
        "gene",
        "taxon:$vals[18]",
        "2018-11-01",
        $vals[0],
        "",
        "");
    print join("\t", @nv)."\n";
        
        
}
