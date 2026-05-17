-- ============================================================
-- NeuroSense AI — Professional Help / Referral Logs
-- Purpose:
-- Store professional help recommendations shown to user
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS public.professional_help_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    wellbeing_checkin_id UUID REFERENCES public.wellbeing_checkins(id) ON DELETE SET NULL,

    urgency TEXT NOT NULL DEFAULT 'none',
    emergency BOOLEAN NOT NULL DEFAULT FALSE,
    needs_professional_help BOOLEAN NOT NULL DEFAULT FALSE,

    issue_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommendations JSONB NOT NULL DEFAULT '[]'::jsonb,
    resources JSONB NOT NULL DEFAULT '[]'::jsonb,

    user_facing_message TEXT,
    disclaimer TEXT,

    source TEXT DEFAULT 'professional_help_api',

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT professional_help_urgency_check
        CHECK (urgency IN (
            'none',
            'routine',
            'soon',
            'urgent',
            'emergency'
        ))
);

CREATE INDEX IF NOT EXISTS idx_professional_help_logs_user_id
ON public.professional_help_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_professional_help_logs_created_at
ON public.professional_help_logs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_professional_help_logs_urgency
ON public.professional_help_logs(urgency);

CREATE INDEX IF NOT EXISTS idx_professional_help_logs_emergency
ON public.professional_help_logs(emergency);

ALTER TABLE public.professional_help_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "professional_help_owner_select"
ON public.professional_help_logs;

CREATE POLICY "professional_help_owner_select"
ON public.professional_help_logs
FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "professional_help_owner_insert"
ON public.professional_help_logs;

CREATE POLICY "professional_help_owner_insert"
ON public.professional_help_logs
FOR INSERT
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "professional_help_owner_delete"
ON public.professional_help_logs;

CREATE POLICY "professional_help_owner_delete"
ON public.professional_help_logs
FOR DELETE
USING (auth.uid() = user_id);