-- ============================================================
-- NeuroSense AI — Report Metadata Table
-- Purpose:
-- Store assessment / solution / combined report metadata
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS public.neurosense_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    report_id TEXT NOT NULL,
    report_type TEXT NOT NULL DEFAULT 'solution',

    format TEXT NOT NULL DEFAULT 'pdf',

    title TEXT,
    summary TEXT,

    risk_level TEXT DEFAULT 'unknown',
    top_emotion TEXT DEFAULT 'neutral',
    mood_trend TEXT DEFAULT 'stable',
    wellbeing_score INTEGER CHECK (
        wellbeing_score IS NULL OR wellbeing_score BETWEEN 0 AND 100
    ),

    file_name TEXT,
    file_path TEXT,
    download_url TEXT,

    report_payload JSONB DEFAULT '{}'::jsonb,

    generated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT neurosense_reports_type_check
        CHECK (report_type IN (
            'assessment',
            'solution',
            'combined',
            'therapy'
        )),

    CONSTRAINT neurosense_reports_format_check
        CHECK (format IN (
            'pdf',
            'csv'
        )),

    CONSTRAINT neurosense_reports_risk_check
        CHECK (risk_level IN (
            'unknown',
            'low',
            'medium',
            'high',
            'crisis'
        ))
);

CREATE INDEX IF NOT EXISTS idx_neurosense_reports_user_id
ON public.neurosense_reports(user_id);

CREATE INDEX IF NOT EXISTS idx_neurosense_reports_report_id
ON public.neurosense_reports(report_id);

CREATE INDEX IF NOT EXISTS idx_neurosense_reports_report_type
ON public.neurosense_reports(report_type);

CREATE INDEX IF NOT EXISTS idx_neurosense_reports_created_at
ON public.neurosense_reports(created_at DESC);

ALTER TABLE public.neurosense_reports ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "neurosense_reports_owner_select"
ON public.neurosense_reports;

CREATE POLICY "neurosense_reports_owner_select"
ON public.neurosense_reports
FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "neurosense_reports_owner_insert"
ON public.neurosense_reports;

CREATE POLICY "neurosense_reports_owner_insert"
ON public.neurosense_reports
FOR INSERT
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "neurosense_reports_owner_update"
ON public.neurosense_reports;

CREATE POLICY "neurosense_reports_owner_update"
ON public.neurosense_reports
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "neurosense_reports_owner_delete"
ON public.neurosense_reports;

CREATE POLICY "neurosense_reports_owner_delete"
ON public.neurosense_reports
FOR DELETE
USING (auth.uid() = user_id);