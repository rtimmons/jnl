package jnl;

require Exporter;
our @ISA = qw(Exporter);
our @EXPORT_OK = qw(dbdir guid open_file);

use FindBin qw($Bin);
use lib "$Bin/../lib";

sub dbdir {
    $ENV{JNL_DB} || "$Bin/../testdb";
}

sub guid {
    my $length = shift || 20;
    my @elts = qw(
        0 1 2 3 4 5 6 7 8 9 A B C D E F G H J K M N P Q R S T U W X Y Z
    );
    my $pid = $$;
    
    my @out = ();
    for( 0 .. $length ) {
        # 13 is an arbitrary prime number
        # 
        # xor in the pid since two instances running at same time
        # might get the same result from rand()
        my $rand = rand( scalar(@elts) * 13 ^ $pid ) % scalar(@elts);
        $out[$_] = $elts[ $rand ];
    }
    join '', @out;
}

sub open_file {
    my ($file) = @_;
    system qq{open -a TextMate "$file"};
}

1