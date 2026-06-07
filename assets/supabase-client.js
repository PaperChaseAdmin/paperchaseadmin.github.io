// PaperChase Supabase Client — Auth + Favourites
// HOW TO SET UP:
// 1. Go to https://supabase.com → Create new project (free tier)
// 2. Copy your project URL + anon key from Settings > API
// 3. Run SQL below in Supabase SQL Editor to create tables
// 4. Fill in SUPABASE_URL and SUPABASE_ANON_KEY below

const SUPABASE_URL = 'https://ksityddelwdtvawjsmyj.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzaXR5ZGRlbHdkdHZhd2pzbXlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg5OTY3NzQsImV4cCI6MjA5NDU3Mjc3NH0.RZMARTP09EeOnKpfS2MwG0IcBcdupIQxDtmCkESM40M';

// --- SQL to run in Supabase SQL Editor ---
/*
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Favourite Bots table
CREATE TABLE IF NOT EXISTS favourite_bots (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  bot_id TEXT NOT NULL,
  bot_name TEXT,
  bot_avatar TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, bot_id)
);

-- Enable Row Level Security
ALTER TABLE favourite_bots ENABLE ROW LEVEL SECURITY;

-- Users can only see their own favourites
CREATE POLICY "Users can view own favourites"
  ON favourite_bots FOR SELECT
  USING (auth.uid() = user_id);

-- Users can insert their own favourites
CREATE POLICY "Users can insert own favourites"
  ON favourite_bots FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can delete their own favourites
CREATE POLICY "Users can delete own favourites"
  ON favourite_bots FOR DELETE
  USING (auth.uid() = user_id);
*/
// --- End SQL ---

// Load Supabase client library
function loadSupabase() {
  return new Promise((resolve, reject) => {
    if (window.supabaseClient) {
      resolve(window.supabaseClient);
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js';
    script.onload = () => {
      if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
        console.warn('Supabase: URL or ANON_KEY not configured. Auth features disabled.');
        resolve(null);
        return;
      }
      const { createClient } = window.supabase;
      window.supabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
      resolve(window.supabaseClient);
    };
    script.onerror = () => reject(new Error('Failed to load Supabase client'));
    document.head.appendChild(script);
  });
}

// ── Auth Functions ──

async function signUp(email, password, displayName) {
  const supabase = await loadSupabase();
  if (!supabase) return { error: 'Supabase not configured' };
  const { data, error } = await supabase.auth.signUp({
    email, password,
    options: { data: { display_name: displayName } }
  });
  return { data, error };
}

async function signIn(email, password) {
  const supabase = await loadSupabase();
  if (!supabase) return { error: 'Supabase not configured' };
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  return { data, error };
}

async function signOut() {
  const supabase = await loadSupabase();
  if (!supabase) return;
  await supabase.auth.signOut();
  window.location.href = window.location.pathname.replace(/\/[^/]*$/, '') + '/';
}

async function getSession() {
  const supabase = await loadSupabase();
  if (!supabase) return null;
  const { data: { session } } = await supabase.auth.getSession();
  return session;
}

// ── Favourite Functions ──

async function addFavourite(botId, botName, botAvatar) {
  const session = await getSession();
  if (!session) return { error: 'Not logged in' };
  const supabase = await loadSupabase();
  if (!supabase) return { error: 'Supabase not configured' };
  const { data, error } = await supabase
    .from('favourite_bots')
    .insert({ user_id: session.user.id, bot_id: botId, bot_name: botName, bot_avatar: botAvatar })
    .select();
  return { data, error };
}

async function removeFavourite(botId) {
  const session = await getSession();
  if (!session) return { error: 'Not logged in' };
  const supabase = await loadSupabase();
  if (!supabase) return { error: 'Supabase not configured' };
  const { error } = await supabase
    .from('favourite_bots')
    .delete()
    .eq('user_id', session.user.id)
    .eq('bot_id', botId);
  return { error };
}

async function getFavourites() {
  const session = await getSession();
  if (!session) return [];
  const supabase = await loadSupabase();
  if (!supabase) return [];
  const { data } = await supabase
    .from('favourite_bots')
    .select('*')
    .eq('user_id', session.user.id)
    .order('created_at', { ascending: false });
  return data || [];
}

async function isFavourite(botId) {
  const session = await getSession();
  if (!session) return false;
  const supabase = await loadSupabase();
  if (!supabase) return false;
  const { data } = await supabase
    .from('favourite_bots')
    .select('id')
    .eq('user_id', session.user.id)
    .eq('bot_id', botId)
    .single();
  return !!data;
}

// ── Session Listener ──
async function initAuth() {
  const supabase = await loadSupabase();
  if (!supabase) return;
  
  supabase.auth.onAuthStateChange((event, session) => {
    // Update UI: toggle login/logout buttons
    const loginItem = document.getElementById('nav-login');
    const registerItem = document.getElementById('nav-register');
    const accountItem = document.getElementById('nav-account');
    const logoutItem = document.getElementById('nav-logout');
    
    if (session) {
      if (loginItem) loginItem.style.display = 'none';
      if (registerItem) registerItem.style.display = 'none';
      if (accountItem) accountItem.style.display = '';
      if (logoutItem) logoutItem.style.display = '';
    } else {
      if (loginItem) loginItem.style.display = '';
      if (registerItem) registerItem.style.display = '';
      if (accountItem) accountItem.style.display = 'none';
      if (logoutItem) logoutItem.style.display = 'none';
    }
  });
}

// Auto-init
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAuth);
} else {
  initAuth();
}

// Export for use in other scripts
window.PaperChaseAuth = {
  signUp, signIn, signOut, getSession, 
  addFavourite, removeFavourite, getFavourites, isFavourite
};
