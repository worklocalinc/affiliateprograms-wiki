import Link from "next/link";
import { Search } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="container mx-auto flex h-16 items-center px-4">
        <Link href="/" className="flex items-center space-x-2">
          <span className="text-xl font-bold text-blue-600">
            AffiliatePrograms.wiki
          </span>
        </Link>

        <nav className="ml-8 hidden md:flex items-center space-x-6">
          <Link
            href="/programs"
            className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
          >
            Programs
          </Link>
          <Link
            href="/categories"
            className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
          >
            Categories
          </Link>
          <Link
            href="/networks"
            className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
          >
            Networks
          </Link>
          <Link
            href="/countries"
            className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
          >
            Countries
          </Link>
        </nav>

        <div className="ml-auto flex items-center space-x-4">
          <Link
            href="/search"
            className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-500 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <Search className="h-4 w-4" />
            <span className="hidden sm:inline">Search programs...</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
