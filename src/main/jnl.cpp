#include <iostream>
#include <vector>

#define BOOST_FILESYSTEM_NO_DEPRECATED 1
#include <boost/filesystem.hpp>
#include <utility>

using std::cout;
using namespace boost::filesystem;
namespace fs = boost::filesystem;

struct tag
{
    std::string mName;
    std::string mValue;
};

struct entry
{
    fs::path            mPath;
    std::vector<tag>    mTags;
};



class database
{
    using entries = std::vector<std::unique_ptr<entry>>;

    const fs::path mRoot;
    entries mEntries;

    explicit database(fs::path root)
    : mRoot{std::move(root)}
    {
        if(!exists(root)) {
            throw std::logic_error("Root " + root.string() + " does not exist");
        }
        if(!is_directory(root)) {
            throw std::logic_error("Root " + root.string() + " is not directory");
        }
    }

    fs::path path(std::string...parts) {
    }
};

int main(int argc, char* argv[])
{
    try {
        ;
    }  catch(const std::exception& e) {
        std::cerr << "Caught " << e.what() << std::endl;
        return -1;
    }  catch(...) {
        std::cerr << "Unknown exception\n" << std::endl;
        return -2;
    }



    path p (current_path());

    try
    {
        auto here = fs::current_path();
        auto s = detail::status(p);
        cout << (s.type() == file_type::file_not_found ? "==" : "!=") << std::endl;
        if (exists(p))
        {
            if (is_regular_file(p))
                cout << p << " size is " << file_size(p) << '\n';

            else if (is_directory(p))
            {
                std::cerr << p << " is a directory containing:\n";
                for (directory_entry& x : boost::filesystem::directory_iterator(p))
                    cout << "    " << x.path() << '\n';
            }
            else
                cout << p << " exists, but is not a regular file or directory\n";
        }
        else
            cout << p << " does not exist\n";
    }

    catch (const filesystem_error& ex)
    {
        cout << ex.what() << '\n';
    }

    return 0;
}