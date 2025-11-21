import React, { useState, useEffect, useMemo } from 'react';
import {
  Search, Plus, Edit2, Save, ArrowLeft, ExternalLink, Globe,
  Clock, DollarSign, Info, Database, Loader2, Bot,
  CheckCircle, XCircle, Terminal, FileJson
} from 'lucide-react';
import { initializeApp } from 'firebase/app';
import {
  getFirestore, collection, addDoc, updateDoc, doc,
  onSnapshot, serverTimestamp, query, deleteDoc
} from 'firebase/firestore';
import {
  getAuth, signInAnonymously, onAuthStateChanged
} from 'firebase/auth';

// ---------------------------------------------------------
// 🔴 REPLACE THIS WITH YOUR FIREBASE CONFIG
// ---------------------------------------------------------
const firebaseConfig = {
  apiKey: "REPLACE_WITH_YOUR_API_KEY",
  authDomain: "REPLACE_WITH_YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "REPLACE_WITH_YOUR_PROJECT_ID",
  storageBucket: "REPLACE_WITH_YOUR_PROJECT_ID.firebasestorage.app",
  messagingSenderId: "REPLACE_WITH_YOUR_SENDER_ID",
  appId: "REPLACE_WITH_YOUR_APP_ID"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

const OPENAPI_SPEC = `openapi: 3.0.1
info:
  title: AffiliateWiki API
  description: API for AI agents to read, write, and review affiliate program data.
  version: '1.0'
servers:
  - url: [https://affiliateprograms.wiki/api](https://affiliateprograms.wiki/api)
paths:
  /programs:
    get:
      summary: Search programs
    post:
      summary: Add a new program
components:
  schemas:
    Program:
      type: object
      properties:
        name: { type: string }
        status: { type: string, enum: [active, review_needed] }`;

export default function AffiliateWiki() {
  const [user, setUser] = useState(null);
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [view, setView] = useState('home');
  const [currentProgramId, setCurrentProgramId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  // --- Auth & Data ---
  useEffect(() => {
    const initAuth = async () => {
      try {
        await signInAnonymously(auth);
      } catch (err) {
        console.error("Auth error", err);
        setError("Auth failed. Check console.");
      }
    };
    initAuth();
    const unsubscribe = onAuthStateChanged(auth, setUser);
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (!user) return;
    const programsRef = collection(db, 'programs');
    const q = query(programsRef);
    const unsubscribe = onSnapshot(q, (snapshot) => {
      setPrograms(snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })));
      setLoading(false);
    }, (err) => {
      console.error(err);
      setError("Permission denied. Check Firestore Rules.");
      setLoading(false);
    });
    return () => unsubscribe();
  }, [user]);

  // --- Derived State ---
  const activeProgram = useMemo(() => programs.find(p => p.id === currentProgramId), [programs, currentProgramId]);

  const filteredPrograms = useMemo(() => {
    let data = programs;
    if (view === 'home') {
       data = programs.filter(p => p.status !== 'review_needed');
    }
    if (!searchQuery) return data.sort((a, b) => (b.updatedAt?.seconds || 0) - (a.updatedAt?.seconds || 0));
    const lowerQuery = searchQuery.toLowerCase();
    return data.filter(p =>
      p.name?.toLowerCase().includes(lowerQuery) ||
      p.niche?.toLowerCase().includes(lowerQuery)
    );
  }, [programs, searchQuery, view]);

  const reviewQueue = useMemo(() => programs.filter(p => p.status === 'review_needed'), [programs]);

  // --- Actions ---
  const handleSave = async (data, asDraft = false) => {
    if (!user) return;
    const programsRef = collection(db, 'programs');
    const timestamp = serverTimestamp();
    const status = asDraft ? 'review_needed' : 'active';
    const payload = { ...data, updatedAt: timestamp, updatedBy: user.uid, status };

    try {
      if (currentProgramId && view === 'edit') {
        await updateDoc(doc(programsRef, currentProgramId), payload);
      } else {
        await addDoc(programsRef, { ...payload, createdAt: timestamp });
      }
      if (!asDraft) setView('view');
    } catch (err) {
      console.error(err);
      alert("Error saving. Check console for permissions issues.");
    }
  };

  const handleApprove = async (id) => {
    const ref = doc(db, 'programs', id);
    await updateDoc(ref, { status: 'active', reviewedBy: user.uid, reviewedAt: serverTimestamp() });
  };

  const handleReject = async (id) => {
    if(confirm("Delete this submission?")) {
      const ref = doc(db, 'programs', id);
      await deleteDoc(ref);
    }
  };

  // --- Views ---
  const Header = () => (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-20 text-white">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <div
          className="flex items-center space-x-2 cursor-pointer"
          onClick={() => { setView('home'); setCurrentProgramId(null); setSearchQuery(''); }}
        >
          <div className="w-8 h-8 bg-indigo-500 rounded-md flex items-center justify-center font-bold text-white">W</div>
          <span className="font-bold text-lg hidden sm:inline">Affiliate<span className="text-indigo-400">Programs</span>.wiki</span>
        </div>

        <nav className="flex items-center space-x-1 sm:space-x-4">
          <button
            onClick={() => setView('review-queue')}
            className={`flex items-center space-x-1 px-3 py-2 rounded-full text-xs sm:text-sm font-medium transition-colors ${view === 'review-queue' ? 'bg-slate-800 text-indigo-400' : 'text-slate-400 hover:text-white'}`}
          >
            <CheckCircle size={16} />
            <span className="hidden sm:inline">Review Queue</span>
            {reviewQueue.length > 0 && (
              <span className="ml-1 bg-indigo-500 text-white text-[10px] px-1.5 py-0.5 rounded-full">{reviewQueue.length}</span>
            )}
          </button>

          <button
            onClick={() => setView('agent-portal')}
            className={`flex items-center space-x-1 px-3 py-2 rounded-full text-xs sm:text-sm font-medium transition-colors ${view === 'agent-portal' ? 'bg-slate-800 text-emerald-400' : 'text-slate-400 hover:text-white'}`}
          >
            <Bot size={16} />
            <span className="hidden sm:inline">Agent Access</span>
          </button>

          <button
            onClick={() => { setCurrentProgramId(null); setView('create'); }}
            className="flex items-center space-x-1 bg-indigo-600 text-white px-3 py-2 rounded-full text-xs sm:text-sm font-medium hover:bg-indigo-700 transition-colors ml-2"
          >
            <Plus size={16} />
            <span className="hidden sm:inline">Add Program</span>
          </button>
        </nav>
      </div>
    </header>
  );

  const HomeView = () => (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="text-center mb-10">
        <h2 className="text-3xl font-extrabold text-slate-900 mb-3">The Collaborative Affiliate Database</h2>
        <p className="text-slate-500">Maintained by humans & AI agents. Open for everyone.</p>
        <div className="mt-6 relative max-w-xl mx-auto">
          <Search className="absolute left-3 top-3.5 text-slate-400 h-5 w-5" />
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm"
            placeholder="Search programs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full flex justify-center py-12 text-slate-400"><Loader2 className="animate-spin mr-2"/> Loading...</div>
        ) : filteredPrograms.length === 0 ? (
          <div className="col-span-full text-center py-12 bg-white rounded-xl border border-dashed border-slate-300">
            <Database className="mx-auto text-slate-300 mb-4 h-12 w-12" />
            <h3 className="text-lg font-medium text-slate-900">No active programs found</h3>
            <p className="text-slate-500 mt-1">Check the Review Queue or add one yourself.</p>
          </div>
        ) : (
          filteredPrograms.map(program => (
            <div
              key={program.id}
              onClick={() => { setCurrentProgramId(program.id); setView('view'); }}
              className="group bg-white rounded-lg border border-slate-200 p-5 hover:border-indigo-400 hover:shadow-lg transition-all cursor-pointer relative"
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-bold text-slate-800 group-hover:text-indigo-700 truncate pr-2">{program.name}</h3>
                <span className="text-xs font-mono bg-slate-100 text-slate-500 px-2 py-1 rounded whitespace-nowrap">{program.niche || 'General'}</span>
              </div>
              <p className="text-slate-600 text-sm line-clamp-3 mb-4 h-15">{program.description || 'No description available.'}</p>
              <div className="flex items-center text-xs text-slate-500 space-x-4 pt-3 border-t border-slate-50">
                <div className="flex items-center"><DollarSign size={12} className="mr-1 text-emerald-600"/>{program.commission || '?'}</div>
                <div className="flex items-center"><Clock size={12} className="mr-1 text-blue-600"/>{program.cookieDuration || '?'}</div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );

  const AgentPortalView = () => {
    const [jsonInput, setJsonInput] = useState('{\n  "name": "AI Generated Program",\n  "niche": "Artificial Intelligence",\n  "commission": "20% Lifetime",\n  "url": "[https://example.com](https://example.com)",\n  "description": "This program was added via the simulated Agent Terminal."\n}');
    const [terminalOutput, setTerminalOutput] = useState(null);

    const simulateAgentPost = async () => {
      setTerminalOutput({ type: 'info', msg: 'Processing agent request...' });
      try {
        const parsed = JSON.parse(jsonInput);
        const programsRef = collection(db, 'programs');
        const timestamp = serverTimestamp();
        const payload = {
          ...parsed,
          updatedAt: timestamp,
          createdAt: timestamp,
          updatedBy: 'AI_Agent_001',
          status: 'review_needed',
          source: 'api_simulation'
        };

        const docRef = await addDoc(programsRef, payload);
        setTerminalOutput({ type: 'success', msg: `HTTP 201 Created\nLocation: /programs/${docRef.id}\nStatus: Queued for Review` });
      } catch (err) {
        setTerminalOutput({ type: 'error', msg: `Error: ${err.message}` });
      }
    };

    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-900 flex items-center">
            <Bot className="mr-2 text-emerald-600" /> Agent & API Portal
          </h2>
          <p className="text-slate-600 mt-2">
            This section allows Large Language Models to discover, read, and contribute to the wiki programmatically.
            Below is the specification an agent would use to interface with this database.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div className="bg-slate-900 rounded-xl overflow-hidden shadow-lg border border-slate-700">
              <div className="bg-slate-800 px-4 py-2 flex items-center justify-between border-b border-slate-700">
                <span className="text-slate-200 text-sm font-mono flex items-center"><FileJson size={14} className="mr-2"/> openapi.yaml</span>
                <span className="text-xs text-slate-400">Read-Only</span>
              </div>
              <pre className="p-4 text-xs sm:text-sm text-emerald-400 font-mono overflow-x-auto h-96">
                {OPENAPI_SPEC}
              </pre>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center">
                <Terminal className="mr-2 text-slate-500" /> Agent Simulator
              </h3>
              <textarea
                value={jsonInput}
                onChange={(e) => setJsonInput(e.target.value)}
                className="w-full h-48 font-mono text-sm p-3 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none mb-4 text-slate-800"
              />
              <button
                onClick={simulateAgentPost}
                className="w-full py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors font-mono text-sm flex items-center justify-center"
              >
                POST /api/programs
              </button>
              {terminalOutput && (
                <div className={`mt-4 p-3 rounded-lg border text-sm font-mono whitespace-pre-wrap ${
                  terminalOutput.type === 'error' ? 'bg-red-50 text-red-700 border-red-200' :
                  terminalOutput.type === 'success' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                  'bg-blue-50 text-blue-700 border-blue-200'
                }`}>
                  {terminalOutput.msg}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const ReviewQueueView = () => (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h2 className="text-2xl font-bold text-slate-900 mb-6 flex items-center">
        <CheckCircle className="mr-2 text-indigo-600" /> Review Queue
        <span className="ml-3 bg-indigo-100 text-indigo-800 text-sm py-1 px-3 rounded-full font-medium">
          {reviewQueue.length} Pending
        </span>
      </h2>
      {reviewQueue.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
          <CheckCircle className="mx-auto text-emerald-400 mb-3 h-12 w-12" />
          <p className="text-slate-600">All caught up! No AI submissions pending review.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reviewQueue.map(item => (
            <div key={item.id} className="bg-white border border-l-4 border-l-indigo-500 border-y-slate-200 border-r-slate-200 rounded-r-lg shadow-sm p-5">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                     <h3 className="text-lg font-bold text-slate-900">{item.name}</h3>
                     {item.source === 'api_simulation' && (
                       <span className="bg-emerald-100 text-emerald-800 text-xs px-2 py-0.5 rounded flex items-center">
                         <Bot size={10} className="mr-1"/> AI Generated
                       </span>
                     )}
                  </div>
                  <p className="text-slate-500 text-sm mb-2">{item.description}</p>
                  <div className="flex gap-4 text-xs text-slate-400 font-mono">
                    <span>Niche: {item.niche}</span>
                    <span>Comm: {item.commission}</span>
                  </div>
                </div>
                <div className="flex flex-col space-y-2 ml-4">
                  <button
                    onClick={() => handleApprove(item.id)}
                    className="flex items-center px-3 py-1.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded text-sm font-medium transition-colors"
                  >
                    <CheckCircle size={14} className="mr-1" /> Approve
                  </button>
                  <button
                    onClick={() => handleReject(item.id)}
                    className="flex items-center px-3 py-1.5 bg-red-50 text-red-700 hover:bg-red-100 rounded text-sm font-medium transition-colors"
                  >
                    <XCircle size={14} className="mr-1" /> Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const EditorView = () => {
    const [formData, setFormData] = useState(
      (view === 'edit' && activeProgram) ? activeProgram : {
      name: '', url: '', niche: '', commission: '', cookieDuration: '',
      network: 'Direct', description: '', payoutMethod: '', minPayout: ''
    });

    const handleSubmit = (e) => {
      e.preventDefault();
      handleSave(formData);
    };

    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <button onClick={() => setView('home')} className="mb-4 text-slate-500 hover:text-slate-800 flex items-center"><ArrowLeft size={16} className="mr-1"/> Cancel</button>
        <div className="bg-white p-6 rounded-xl shadow-lg border border-slate-200">
          <h2 className="text-xl font-bold mb-6 text-slate-900">{view === 'edit' ? 'Edit Program' : 'Add New Program'}</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">Name</label>
              <input required className="w-full p-2 border rounded mt-1" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
            </div>
            <div className="grid grid-cols-2 gap-4">
               <div>
                <label className="block text-sm font-medium text-slate-700">Niche</label>
                <input className="w-full p-2 border rounded mt-1" value={formData.niche} onChange={e => setFormData({...formData, niche: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">Commission</label>
                <input className="w-full p-2 border rounded mt-1" value={formData.commission} onChange={e => setFormData({...formData, commission: e.target.value})} />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Description</label>
              <textarea className="w-full p-2 border rounded mt-1" rows="4" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
            </div>
            <button type="submit" className="w-full py-2 bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700">Save Program</button>
          </form>
        </div>
      </div>
    );
  };

  const DetailView = () => {
    if (!activeProgram) return null;
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <button onClick={() => setView('home')} className="mb-4 text-slate-500 flex items-center"><ArrowLeft size={16} className="mr-1"/> Back</button>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-8">
            <div className="flex justify-between items-start mb-6">
              <h1 className="text-3xl font-bold text-slate-900">{activeProgram.name}</h1>
              <button onClick={() => setView('edit')} className="flex items-center text-slate-500 hover:text-indigo-600 border px-3 py-1 rounded"><Edit2 size={14} className="mr-2"/> Edit</button>
            </div>
            <div className="grid grid-cols-3 gap-4 mb-8">
              <div className="p-3 bg-slate-50 rounded border border-slate-100">
                <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Commission</div>
                <div className="font-medium text-slate-800">{activeProgram.commission || 'N/A'}</div>
              </div>
              <div className="p-3 bg-slate-50 rounded border border-slate-100">
                 <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Cookie</div>
                <div className="font-medium text-slate-800">{activeProgram.cookieDuration || 'N/A'}</div>
              </div>
              <div className="p-3 bg-slate-50 rounded border border-slate-100">
                 <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Network</div>
                <div className="font-medium text-slate-800">{activeProgram.network || 'Direct'}</div>
              </div>
            </div>
            <div className="prose prose-slate max-w-none">
              <h3 className="text-lg font-bold">About the Program</h3>
              <p className="whitespace-pre-wrap">{activeProgram.description}</p>
            </div>
          </div>
          <div className="bg-slate-50 px-8 py-4 border-t border-slate-200 flex justify-between text-xs text-slate-400">
            <span>ID: {activeProgram.id}</span>
            <span>Status: {activeProgram.status}</span>
          </div>
        </div>
      </div>
    );
  };

  if (error) return <div className="flex h-screen items-center justify-center text-red-500">{error}</div>;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      <Header />
      <main>
        {view === 'home' && <HomeView />}
        {view === 'agent-portal' && <AgentPortalView />}
        {view === 'review-queue' && <ReviewQueueView />}
        {view === 'create' || view === 'edit' ? <EditorView /> : null}
        {view === 'view' && <DetailView />}
      </main>
    </div>
  );
}
