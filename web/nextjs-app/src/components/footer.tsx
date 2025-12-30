import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t bg-white mt-16">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Browse</h3>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/programs"
                  className="text-gray-600 hover:text-blue-600"
                >
                  All Programs
                </Link>
              </li>
              <li>
                <Link
                  href="/categories"
                  className="text-gray-600 hover:text-blue-600"
                >
                  Categories
                </Link>
              </li>
              <li>
                <Link
                  href="/networks"
                  className="text-gray-600 hover:text-blue-600"
                >
                  Networks
                </Link>
              </li>
              <li>
                <Link
                  href="/countries"
                  className="text-gray-600 hover:text-blue-600"
                >
                  Countries
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-4">
              Popular Categories
            </h3>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/categories/e-commerce"
                  className="text-gray-600 hover:text-blue-600"
                >
                  E-Commerce
                </Link>
              </li>
              <li>
                <Link
                  href="/categories/software"
                  className="text-gray-600 hover:text-blue-600"
                >
                  Software
                </Link>
              </li>
              <li>
                <Link
                  href="/categories/finance"
                  className="text-gray-600 hover:text-blue-600"
                >
                  Finance
                </Link>
              </li>
              <li>
                <Link
                  href="/categories/health"
                  className="text-gray-600 hover:text-blue-600"
                >
                  Health
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Top Networks</h3>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/networks/shareasale"
                  className="text-gray-600 hover:text-blue-600"
                >
                  ShareASale
                </Link>
              </li>
              <li>
                <Link
                  href="/networks/cj-affiliate"
                  className="text-gray-600 hover:text-blue-600"
                >
                  CJ Affiliate
                </Link>
              </li>
              <li>
                <Link
                  href="/networks/impact"
                  className="text-gray-600 hover:text-blue-600"
                >
                  Impact
                </Link>
              </li>
              <li>
                <Link
                  href="/networks/awin"
                  className="text-gray-600 hover:text-blue-600"
                >
                  Awin
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Resources</h3>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/about"
                  className="text-gray-600 hover:text-blue-600"
                >
                  About
                </Link>
              </li>
              <li>
                <a
                  href="/docs"
                  className="text-gray-600 hover:text-blue-600"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  API Docs
                </a>
              </li>
              <li>
                <Link
                  href="/privacy"
                  className="text-gray-600 hover:text-blue-600"
                >
                  Privacy
                </Link>
              </li>
              <li>
                <Link
                  href="/terms"
                  className="text-gray-600 hover:text-blue-600"
                >
                  Terms
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t text-center text-gray-500 text-sm">
          <p>
            &copy; {new Date().getFullYear()} AffiliatePrograms.wiki. All rights
            reserved.
          </p>
          <p className="mt-2">
            Data updated daily. 36,000+ affiliate programs indexed.
          </p>
        </div>
      </div>
    </footer>
  );
}
