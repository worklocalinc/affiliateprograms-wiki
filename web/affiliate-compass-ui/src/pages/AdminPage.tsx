import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  CheckCircle,
  XCircle,
  Clock,
  FileText,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "https://api.affiliateprograms.wiki";

interface Proposal {
  id: string;
  entity_type: string;
  entity_id: number;
  entity_name: string;
  changes: Record<string, unknown>;
  sources: Array<{ url: string; captured_at?: string }>;
  reasoning: string;
  status: string;
  created_at: string;
  reviewed_at?: string;
  review_notes?: string;
}

interface EditorialStats {
  proposals: {
    pending_review: number;
    approved: number;
    pending_seo: number;
    published: number;
    rejected: number;
  };
  history: {
    total_changes: number;
  };
  verification: {
    broken_urls: number;
  };
  link_rules: {
    active: number;
  };
}

const statusColors: Record<string, string> = {
  pending_review: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  pending_seo: "bg-blue-100 text-blue-800",
  published: "bg-purple-100 text-purple-800",
  rejected: "bg-red-100 text-red-800",
};

export default function AdminPage() {
  const [agentKey, setAgentKey] = useState(localStorage.getItem("agent_key") || "");
  const [stats, setStats] = useState<EditorialStats | null>(null);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("pending_review");

  const fetchWithAuth = async (path: string, options: RequestInit = {}) => {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "X-Agent-Key": agentKey,
        ...options.headers,
      },
    });
    if (!res.ok) {
      throw new Error(`API error: ${res.status}`);
    }
    return res.json();
  };

  const loadStats = async () => {
    try {
      const data = await fetchWithAuth("/editorial/stats");
      setStats(data);
    } catch (e) {
      console.error("Failed to load stats:", e);
    }
  };

  const loadProposals = async (status: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWithAuth(`/editorial/proposals?status=${status}&limit=50`);
      setProposals(data.items || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load proposals");
      setProposals([]);
    } finally {
      setLoading(false);
    }
  };

  const reviewProposal = async (proposalId: string, decision: "approve" | "reject", notes: string = "") => {
    try {
      await fetchWithAuth(`/editorial/proposals/${proposalId}/review`, {
        method: "POST",
        body: JSON.stringify({ decision, notes }),
      });
      // Refresh
      loadStats();
      loadProposals(activeTab);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to review proposal");
    }
  };

  const publishProposal = async (proposalId: string) => {
    try {
      await fetchWithAuth(`/editorial/proposals/${proposalId}/publish`, {
        method: "POST",
      });
      loadStats();
      loadProposals(activeTab);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to publish proposal");
    }
  };

  useEffect(() => {
    if (agentKey) {
      localStorage.setItem("agent_key", agentKey);
      loadStats();
      loadProposals(activeTab);
    }
  }, [agentKey]);

  useEffect(() => {
    if (agentKey) {
      loadProposals(activeTab);
    }
  }, [activeTab]);

  if (!agentKey) {
    return (
      <div className="container mx-auto py-8 max-w-md">
        <Card>
          <CardHeader>
            <CardTitle>Admin Login</CardTitle>
            <CardDescription>Enter your agent key to access the admin dashboard</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              type="password"
              placeholder="Agent Key (e.g., ak_admin_default)"
              value={agentKey}
              onChange={(e) => setAgentKey(e.target.value)}
            />
            <Button onClick={() => setAgentKey(agentKey)} className="w-full">
              Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Editorial Dashboard</h1>
          <p className="text-muted-foreground">Review and manage content proposals</p>
        </div>
        <Button variant="outline" onClick={() => { loadStats(); loadProposals(activeTab); }}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Pending Review</CardDescription>
              <CardTitle className="text-2xl text-yellow-600">
                {stats.proposals.pending_review}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Approved</CardDescription>
              <CardTitle className="text-2xl text-green-600">
                {stats.proposals.approved}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Published</CardDescription>
              <CardTitle className="text-2xl text-purple-600">
                {stats.proposals.published}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Broken URLs</CardDescription>
              <CardTitle className="text-2xl text-red-600">
                {stats.verification.broken_urls}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Link Rules</CardDescription>
              <CardTitle className="text-2xl text-blue-600">
                {stats.link_rules.active}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Proposals */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="pending_review">
            <Clock className="h-4 w-4 mr-2" />
            Pending ({stats?.proposals.pending_review || 0})
          </TabsTrigger>
          <TabsTrigger value="approved">
            <CheckCircle className="h-4 w-4 mr-2" />
            Approved ({stats?.proposals.approved || 0})
          </TabsTrigger>
          <TabsTrigger value="published">
            <FileText className="h-4 w-4 mr-2" />
            Published ({stats?.proposals.published || 0})
          </TabsTrigger>
          <TabsTrigger value="rejected">
            <XCircle className="h-4 w-4 mr-2" />
            Rejected ({stats?.proposals.rejected || 0})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4 mt-4">
          {loading ? (
            <div className="text-center py-8">Loading...</div>
          ) : proposals.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No proposals in this status
            </div>
          ) : (
            proposals.map((proposal) => (
              <ProposalCard
                key={proposal.id}
                proposal={proposal}
                onApprove={() => reviewProposal(proposal.id, "approve")}
                onReject={(notes) => reviewProposal(proposal.id, "reject", notes)}
                onPublish={() => publishProposal(proposal.id)}
              />
            ))
          )}
        </TabsContent>
      </Tabs>

      {/* Logout */}
      <div className="pt-4 border-t">
        <Button
          variant="ghost"
          onClick={() => {
            localStorage.removeItem("agent_key");
            setAgentKey("");
          }}
        >
          Logout
        </Button>
      </div>
    </div>
  );
}

function ProposalCard({
  proposal,
  onApprove,
  onReject,
  onPublish,
}: {
  proposal: Proposal;
  onApprove: () => void;
  onReject: (notes: string) => void;
  onPublish: () => void;
}) {
  const [rejectNotes, setRejectNotes] = useState("");
  const [showReject, setShowReject] = useState(false);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {proposal.entity_name}
              <Badge variant="outline">{proposal.entity_type}</Badge>
              <Badge className={statusColors[proposal.status]}>{proposal.status}</Badge>
            </CardTitle>
            <CardDescription>
              ID: {proposal.id.slice(0, 8)}... |{" "}
              {new Date(proposal.created_at).toLocaleDateString()}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Changes */}
        <div>
          <h4 className="font-semibold mb-2">Proposed Changes</h4>
          <pre className="text-sm bg-muted p-3 rounded overflow-x-auto">
            {JSON.stringify(proposal.changes, null, 2)}
          </pre>
        </div>

        {/* Reasoning */}
        {proposal.reasoning && (
          <div>
            <h4 className="font-semibold mb-2">Reasoning</h4>
            <p className="text-sm text-muted-foreground">{proposal.reasoning}</p>
          </div>
        )}

        {/* Sources */}
        {proposal.sources && proposal.sources.length > 0 && (
          <div>
            <h4 className="font-semibold mb-2">Sources</h4>
            <ul className="text-sm space-y-1">
              {proposal.sources.map((source, i) => (
                <li key={i} className="flex items-center gap-2">
                  <ExternalLink className="h-3 w-3" />
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline truncate"
                  >
                    {source.url}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actions */}
        {proposal.status === "pending_review" && (
          <div className="flex gap-2 pt-2 border-t">
            <Button onClick={onApprove} className="bg-green-600 hover:bg-green-700">
              <CheckCircle className="h-4 w-4 mr-2" />
              Approve
            </Button>
            {!showReject ? (
              <Button variant="outline" onClick={() => setShowReject(true)}>
                <XCircle className="h-4 w-4 mr-2" />
                Reject
              </Button>
            ) : (
              <div className="flex gap-2 flex-1">
                <Input
                  placeholder="Rejection reason..."
                  value={rejectNotes}
                  onChange={(e) => setRejectNotes(e.target.value)}
                />
                <Button
                  variant="destructive"
                  onClick={() => {
                    onReject(rejectNotes);
                    setShowReject(false);
                  }}
                >
                  Confirm Reject
                </Button>
              </div>
            )}
          </div>
        )}

        {proposal.status === "approved" && (
          <div className="flex gap-2 pt-2 border-t">
            <Button onClick={onPublish} className="bg-purple-600 hover:bg-purple-700">
              <FileText className="h-4 w-4 mr-2" />
              Publish
            </Button>
          </div>
        )}

        {/* Review Notes */}
        {proposal.review_notes && (
          <div className="pt-2 border-t">
            <h4 className="font-semibold mb-1">Review Notes</h4>
            <p className="text-sm text-muted-foreground">{proposal.review_notes}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
