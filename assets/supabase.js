/* PaperChase Supabase Auth Helper */
const SUPABASE_URL = 'https://ksityddelwdtvawjsmyj.supabase.co';
const SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzE4MjM2ODAwLAogICJleHAiOiAxODc2MDAzMjAwCn0.sG8T5q0ZAqLR4JpYbDqh7lA64voYv5RjaM1MpFnpr5I';

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
