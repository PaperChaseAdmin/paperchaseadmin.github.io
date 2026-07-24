-- =============================================
-- PaperChase Auth Schema — Run in Supabase SQL Editor
-- =============================================

-- 1. Profiles table
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  avatar TEXT DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Saved bots (favorites)
CREATE TABLE IF NOT EXISTS public.saved_bots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  bot_id TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, bot_id)
);

-- 3. Alert preferences
CREATE TABLE IF NOT EXISTS public.alert_prefs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE,
  market_alerts BOOLEAN DEFAULT false,
  bot_alerts BOOLEAN DEFAULT false,
  alert_email TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Email notification log
CREATE TABLE IF NOT EXISTS public.notification_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  alert_type TEXT NOT NULL,
  message TEXT,
  sent_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── RLS (Row Level Security) ──
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_bots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alert_prefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_log ENABLE ROW LEVEL SECURITY;

-- Profiles: users can read & update own
CREATE POLICY "users can read own profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id);
CREATE POLICY "users can update own profile" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "users can insert own profile" ON public.profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

-- Saved bots: users can CRUD own
CREATE POLICY "users can read own saved bots" ON public.saved_bots
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "users can insert own saved bots" ON public.saved_bots
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "users can delete own saved bots" ON public.saved_bots
  FOR DELETE USING (auth.uid() = user_id);

-- Alert prefs: users can CRUD own
CREATE POLICY "users can read own alert prefs" ON public.alert_prefs
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "users can insert own alert prefs" ON public.alert_prefs
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "users can update own alert prefs" ON public.alert_prefs
  FOR UPDATE USING (auth.uid() = user_id);

-- Notification log: users can read own
CREATE POLICY "users can read own notifications" ON public.notification_log
  FOR SELECT USING (auth.uid() = user_id);

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name, avatar)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1)),
    ''
  );
  INSERT INTO public.alert_prefs (user_id, alert_email)
  VALUES (NEW.id, NEW.email);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
