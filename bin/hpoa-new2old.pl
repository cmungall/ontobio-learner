#!/usr/bin/perl
while(<>) {
    chomp;
    if (m@\[(\d\d\d\d-\d\d-\d\d)\]@) {
        $_ .= "$1";
    }
    else {
        $_ .= "\t2018-11-11";
    }
    print "$_\n";
}
