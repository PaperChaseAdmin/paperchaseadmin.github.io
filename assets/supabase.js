/* PaperChase Supabase Auth Helper */
const SUPABASE_URL = 'https://ksityddelwdtvawjsmyj.supabase.co';
const SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzaXR5ZGRlbHdkdHZhd2pzbXlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg5OTY3NzQsImV4cCI6MjA5NDU3Mjc3NH0.RZMARTP09EeOnKpfS2MwG0IcBcdupIQxDtmCkESM40M';

let _supabase = null;
function getSupabase() {
  if (!_supabase) {
    _supabase = supabase.createClient(SUPABASE_URL, SUPABASE_ANON);
  }
  return _supabase;
}

async function checkSession() {
  const sb = getSupabase();
  const { data: { session } } = await sb.auth.getSession();
  return session;
}

async function signIn(email, password) {
  const sb = getSupabase();
  const { data, error } = await sb.auth.signInWithPassword({ email, password });
  return { data, error };
}

async function signUp(email, password, displayName) {
  const sb = getSupabase();
  const { data, error } = await sb.auth.signUp({
    email, password,
    options: { data: { display_name: displayName } }
  });
  return { data, error };
}

async function signOut() {
  const sb = getSupabase();
  await sb.auth.signOut();
}

function requireAuth() {
  checkSession().then(session => {
    if (!session) {
      window.location.href = '/login/?redirect=' + encodeURIComponent(window.location.pathname);
    }
  });
}
