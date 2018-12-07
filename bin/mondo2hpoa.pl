#!/usr/bin/perl
while(<>) {
    chomp;
    if (m@^id: (\S+)@) {
        $id = $1;
    }
    if (m@^xref: OMIM:(\S+)@) {
        $x = $1;
        print "OMIM\t$x\t$x\t\t$id\t$id\tIEA\t\t\t\tO\t\tCJM\n";
    }
}
