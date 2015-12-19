package jnl;

require Exporter;
our @ISA = qw(Exporter);
our @EXPORT_OK = qw(dbdir guid open_file open_dir today);

use FindBin qw($Bin);
use lib "$Bin/../lib";

use Carp::Heavy;
use Date::Parse;

sub dbdir {
    my ($subdir) = @_;
    my $root = $ENV{JNL_DB} || "$Bin/../testdb";
    if ( ! -d "$root" ) {
        croak("Invalid root directory $root");
    }
    if ( !defined($subdir) ) {
        return $root;
    }
    my $out = "$root/$subdir";
    if ( ! -d $out ) {
        if ( !mkdir($out) ) {
            croak("Couldn't create $out: $!");
        }
    }
    return $out;
}

# TODO: name is bad
sub today {
    my ($date) = @_;
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst);
    
    if ( !defined($date) ) {
        # use today's date
        ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) =
            localtime(time);
    }
    else {
        # IDEA: support Date::Manip or ParseDateString etc stuff so can enter "yesterday" etc
        # annoying that strptime and localtime aren't compatible (are they?)
        ($sec,$min,$hour,$mday,$mon,$year,$zone) = strptime($date); 
    }
    
    $year += 1900;
    $mon  += 1;
    $mon  = sprintf("%02d", $mon);
    $mday = sprintf("%02d", $mday);
    return "$year-$mon-$mday";
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

sub open_dir {
    my ($subdir) = @_;
    $subdir = dbdir($subdir);
    system qq{open -a Finder "$subdir"};
}

sub open_file {
    my ($file) = @_;
    system qq{open -a TextMate "$file"};
}


1
