-- ============================================================
-- NeuroSense AI — Wellbeing Check-ins Table
-- Purpose:
-- Store user's Mental & Social Wellbeing Check-In responses
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS public.wellbeing_checkins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    mood TEXT NOT NULL DEFAULT 'neutral',
    stress INTEGER NOT NULL DEFAULT 3 CHECK (stress BETWEEN 1 AND 5),
    social_connection INTEGER NOT NULL DEFAULT 3 CHECK (social_connection BETWEEN 1 AND 5),
    sleep TEXT NOT NULL DEFAULT 'okay',
    concerns JSONB NOT NULL DEFAULT '[]'::jsonb,
    emotional_safety INTEGER NOT NULL DEFAULT 3 CHECK (emotional_safety BETWEEN 1 AND 5),
    support_available TEXT NOT NULL DEFAULT 'maybe',

    current_thoughts TEXT,

    wellbeing_score INTEGER NOT NULL DEFAULT 50 CHECK (wellbeing_score BETWEEN 0 AND 100),
    risk_level TEXT NOT NULL DEFAULT 'medium',

    score_explanation JSONB DEFAULT '{}'::jsonb,
    risk_explanation TEXT,

    source TEXT DEFAULT 'mode_checkin',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT wellbeing_checkins_mood_check
        CHECK (mood IN (
            'happy',
            'calm',
            'neutral',
            'sad',
            'anxious',
            'angry',
            'overwhelmed'
        )),

    CONSTRAINT wellbeing_checkins_sleep_check
        CHECK (sleep IN (
            'good',
            'okay',
            'poor',
            'very_poor'
        )),

    CONSTRAINT wellbeing_checkins_support_check
        CHECK (support_available IN (
            'yes',
            'maybe',
            'no'
        )),

    CONSTRAINT wellbeing_checkins_risk_check
        CHECK (risk_level IN (
            'low',
            'medium',
            'high'
        ))
);

CREATE INDEX IF NOT EXISTS idx_wellbeing_checkins_user_id
ON public.wellbeing_checkins(user_id);

CREATE INDEX IF NOT EXISTS idx_wellbeing_checkins_created_at
ON public.wellbeing_checkins(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_wellbeing_checkins_risk_level
ON public.wellbeing_checkins(risk_level);

CREATE OR REPLACE FUNCTION public.set_wellbeing_checkins_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_wellbeing_checkins_updated_at
ON public.wellbeing_checkins;

CREATE TRIGGER trg_wellbeing_checkins_updated_at
BEFORE UPDATE ON public.wellbeing_checkins
FOR EACH ROW
EXECUTE FUNCTION public.set_wellbeing_checkins_updated_at();

ALTER TABLE public.wellbeing_checkins ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "wellbeing_owner_select"
ON public.wellbeing_checkins;

CREATE POLICY "wellbeing_owner_select"
ON public.wellbeing_checkins
FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "wellbeing_owner_insert"
ON public.wellbeing_checkins;

CREATE POLICY "wellbeing_owner_insert"
ON public.wellbeing_checkins
FOR INSERT
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "wellbeing_owner_update"
ON public.wellbeing_checkins;

CREATE POLICY "wellbeing_owner_update"
ON public.wellbeing_checkins
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "wellbeing_owner_delete"
ON public.wellbeing_checkins;

CREATE POLICY "wellbeing_owner_delete"
ON public.wellbeing_checkins
FOR DELETE
USING (auth.uid() = user_id);