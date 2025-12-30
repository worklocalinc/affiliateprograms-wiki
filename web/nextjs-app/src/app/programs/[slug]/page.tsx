import { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import { notFound } from "next/navigation";
import {
  ExternalLink,
  Clock,
  DollarSign,
  Tag,
  Globe,
  CreditCard,
  Calendar,
  Shield,
  Languages,
  MapPin,
  ChevronRight,
  CheckCircle,
} from "lucide-react";
import { getProgram } from "@/lib/api";
import { generateProgramMetadata, generateProgramJsonLd, generateBreadcrumbJsonLd } from "@/lib/seo";
import { rewriteUrl } from "@/lib/link-rewriter";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const program = await getProgram(slug);
  if (!program) return {};
  return generateProgramMetadata(program);
}

export const revalidate = 300;

export default async function ProgramPage({ params }: PageProps) {
  const { slug } = await params;
  const program = await getProgram(slug);

  if (!program) {
    notFound();
  }

  // Rewrite signup URL with affiliate link if rule exists
  const affiliateUrl = program.signup_url
    ? await rewriteUrl(program.signup_url)
    : null;

  const breadcrumbs = [
    { name: "Home", url: "https://affiliateprograms.wiki" },
    { name: "Programs", url: "https://affiliateprograms.wiki/programs" },
    { name: program.name, url: `https://affiliateprograms.wiki/programs/${program.slug}` },
  ];

  return (
    <>
      {/* JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(generateProgramJsonLd(program)),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(generateBreadcrumbJsonLd(breadcrumbs)),
        }}
      />

      <div className="max-w-4xl mx-auto space-y-8">
        {/* Breadcrumbs */}
        <nav className="flex items-center gap-2 text-sm text-gray-500">
          <Link href="/" className="hover:text-blue-600">
            Home
          </Link>
          <ChevronRight className="h-4 w-4" />
          <Link href="/programs" className="hover:text-blue-600">
            Programs
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-gray-900">{program.name}</span>
        </nav>

        {/* Header */}
        <div className="bg-white rounded-xl border shadow-sm p-6 md:p-8">
          <div className="flex flex-col md:flex-row gap-6">
            {/* Logo */}
            <div className="flex-shrink-0 w-20 h-20 bg-gray-100 rounded-xl flex items-center justify-center overflow-hidden">
              {program.logo_url ? (
                <Image
                  src={program.logo_url}
                  alt={program.name}
                  width={80}
                  height={80}
                  className="object-contain"
                />
              ) : (
                <span className="text-3xl font-bold text-gray-400">
                  {program.name.charAt(0)}
                </span>
              )}
            </div>

            {/* Title & Domain */}
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900">{program.name}</h1>
              {program.domain && (
                <p className="text-gray-500 mt-1 flex items-center gap-1">
                  <Globe className="h-4 w-4" />
                  {program.domain}
                </p>
              )}

              {/* Quick Stats */}
              <div className="mt-4 flex flex-wrap gap-4">
                {program.commission_rate && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-100 text-green-700 rounded-full font-medium">
                    <DollarSign className="h-4 w-4" />
                    {program.commission_rate}
                  </span>
                )}
                {program.cookie_duration_days && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full font-medium">
                    <Clock className="h-4 w-4" />
                    {program.cookie_duration_days}-day cookie
                  </span>
                )}
                {program.tracking_platform && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-purple-100 text-purple-700 rounded-full font-medium">
                    <Tag className="h-4 w-4" />
                    {program.tracking_platform}
                  </span>
                )}
              </div>
            </div>

            {/* CTA */}
            {affiliateUrl && (
              <div className="flex-shrink-0">
                <a
                  href={affiliateUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Join Program
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Commission Details */}
          <div className="bg-white rounded-xl border shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-green-600" />
              Commission Details
            </h2>
            <dl className="space-y-3">
              {program.commission_rate && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Commission Rate</dt>
                  <dd className="font-medium text-gray-900">{program.commission_rate}</dd>
                </div>
              )}
              {program.payout_model && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Payout Model</dt>
                  <dd className="font-medium text-gray-900">{program.payout_model}</dd>
                </div>
              )}
              {program.minimum_payout && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Minimum Payout</dt>
                  <dd className="font-medium text-gray-900">{program.minimum_payout}</dd>
                </div>
              )}
              {program.payment_frequency && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Payment Frequency</dt>
                  <dd className="font-medium text-gray-900">{program.payment_frequency}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Tracking Details */}
          <div className="bg-white rounded-xl border shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-600" />
              Tracking Details
            </h2>
            <dl className="space-y-3">
              {program.cookie_duration_days && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Cookie Duration</dt>
                  <dd className="font-medium text-gray-900">{program.cookie_duration_days} days</dd>
                </div>
              )}
              {program.tracking_platform && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Tracking Platform</dt>
                  <dd className="font-medium text-gray-900">{program.tracking_platform}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Payment Methods */}
          {program.payment_methods && program.payment_methods.length > 0 && (
            <div className="bg-white rounded-xl border shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-orange-600" />
                Payment Methods
              </h2>
              <div className="flex flex-wrap gap-2">
                {program.payment_methods.map((method) => (
                  <span
                    key={method}
                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                  >
                    {method}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Requirements */}
          {program.requirements && (
            <div className="bg-white rounded-xl border shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Shield className="h-5 w-5 text-purple-600" />
                Requirements
              </h2>
              <p className="text-gray-700">{program.requirements}</p>
            </div>
          )}

          {/* Restrictions */}
          {program.restrictions && (
            <div className="bg-white rounded-xl border shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Shield className="h-5 w-5 text-red-600" />
                Restrictions
              </h2>
              <p className="text-gray-700">{program.restrictions}</p>
            </div>
          )}

          {/* Languages */}
          {program.languages && program.languages.length > 0 && (
            <div className="bg-white rounded-xl border shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Languages className="h-5 w-5 text-teal-600" />
                Languages
              </h2>
              <div className="flex flex-wrap gap-2">
                {program.languages.map((lang) => (
                  <span
                    key={lang}
                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                  >
                    {lang}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Countries */}
          {program.countries && program.countries.length > 0 && (
            <div className="bg-white rounded-xl border shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <MapPin className="h-5 w-5 text-pink-600" />
                Available Countries
              </h2>
              <div className="flex flex-wrap gap-2">
                {program.countries.slice(0, 10).map((country) => (
                  <Link
                    key={country}
                    href={`/countries/${encodeURIComponent(country)}`}
                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200 transition-colors"
                  >
                    {country}
                  </Link>
                ))}
                {program.countries.length > 10 && (
                  <span className="px-3 py-1 bg-gray-100 text-gray-500 rounded-full text-sm">
                    +{program.countries.length - 10} more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Categories */}
        {program.categories && program.categories.length > 0 && (
          <div className="bg-white rounded-xl border shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Categories</h2>
            <div className="flex flex-wrap gap-2">
              {program.categories.map((category) => (
                <Link
                  key={category}
                  href={`/categories/${category.toLowerCase().replace(/\s+/g, "-")}`}
                  className="px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors"
                >
                  {category}
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Deep Research Badge */}
        {program.deep_researched_at && (
          <div className="bg-green-50 rounded-xl border border-green-200 p-4 flex items-center gap-3">
            <CheckCircle className="h-6 w-6 text-green-600 flex-shrink-0" />
            <div>
              <p className="font-medium text-green-900">Deep Researched</p>
              <p className="text-sm text-green-700">
                This program was thoroughly researched on{" "}
                {new Date(program.deep_researched_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </p>
            </div>
          </div>
        )}

        {/* CTA Footer */}
        {affiliateUrl && (
          <div className="bg-blue-600 rounded-xl p-6 md:p-8 text-center text-white">
            <h2 className="text-2xl font-bold mb-2">Ready to Start Earning?</h2>
            <p className="text-blue-100 mb-6">
              Join the {program.name} affiliate program and start earning{" "}
              {program.commission_rate || "commissions"} today.
            </p>
            <a
              href={affiliateUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-8 py-3 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-medium"
            >
              Join {program.name}
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        )}
      </div>
    </>
  );
}
