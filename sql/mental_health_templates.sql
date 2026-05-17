-- ============================================================
-- NeuroSense AI — Research Chat + Mental Health Templates
-- Purpose:
-- Store custom templates, research chat history, and template usage logs
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 1. Custom Mental Health Templates
-- ============================================================

CREATE TABLE IF NOT EXISTS public.mental_health_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    template_key TEXT UNIQUE,
    title TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'stress',
    description TEXT,
    prompt TEXT NOT NULL,
    output_type TEXT NOT NULL DEFAULT 'plan',

    risk_level TEXT NOT NULL DEFAULT 'low',
    is_prebuilt BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    usage_count INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT mental_health_templates_category_check
        CHECK (category IN (
            'stress',
            'anxiety',
            'sleep',
            'loneliness',
            'academic_pressure',
            'relationship',
            'self_doubt',
            'anger',
            'mood_tracking',
            'professional_help',
            'crisis_safety',
            'weekly_reflection'
        )),

    CONSTRAINT mental_health_templates_output_type_check
        CHECK (output_type IN (
            'plan',
            'checklist',
            'reflection',
            'guide',
            'journal_prompt',
            'safety_plan'
        )),

    CONSTRAINT mental_health_templates_risk_level_check
        CHECK (risk_level IN (
            'low',
            'medium',
            'high'
        ))
);

CREATE INDEX IF NOT EXISTS idx_mental_health_templates_user_id
ON public.mental_health_templates(user_id);

CREATE INDEX IF NOT EXISTS idx_mental_health_templates_category
ON public.mental_health_templates(category);

CREATE INDEX IF NOT EXISTS idx_mental_health_templates_is_active
ON public.mental_health_templates(is_active);

CREATE INDEX IF NOT EXISTS idx_mental_health_templates_created_at
ON public.mental_health_templates(created_at DESC);


-- ============================================================
-- 2. Research Chat History
-- ============================================================

CREATE TABLE IF NOT EXISTS public.research_chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    template_id UUID REFERENCES public.mental_health_templates(id) ON DELETE SET NULL,

    template_key TEXT,
    template_title TEXT,

    query TEXT NOT NULL,
    answer TEXT NOT NULL,

    model TEXT,
    used_ollama BOOLEAN NOT NULL DEFAULT TRUE,

    risk_level TEXT DEFAULT 'none',
    safety JSONB DEFAULT '{}'::jsonb,
    professional_help JSONB DEFAULT '{}'::jsonb,
    agent_trace JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT research_chat_history_risk_level_check
        CHECK (risk_level IN (
            'none',
            'low',
            'medium',
            'high',
            'crisis'
        ))
);

CREATE INDEX IF NOT EXISTS idx_research_chat_history_user_id
ON public.research_chat_history(user_id);

CREATE INDEX IF NOT EXISTS idx_research_chat_history_template_id
ON public.research_chat_history(template_id);

CREATE INDEX IF NOT EXISTS idx_research_chat_history_created_at
ON public.research_chat_history(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_research_chat_history_risk_level
ON public.research_chat_history(risk_level);


-- ============================================================
-- 3. Template Run Logs
-- ============================================================

CREATE TABLE IF NOT EXISTS public.template_run_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    template_id UUID REFERENCES public.mental_health_templates(id) ON DELETE SET NULL,

    template_key TEXT,
    template_title TEXT,

    query TEXT NOT NULL,
    output TEXT NOT NULL,

    model TEXT,
    used_ollama BOOLEAN DEFAULT TRUE,

    risk_level TEXT DEFAULT 'none',
    safety JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT template_run_logs_risk_level_check
        CHECK (risk_level IN (
            'none',
            'low',
            'medium',
            'high',
            'crisis'
        ))
);

CREATE INDEX IF NOT EXISTS idx_template_run_logs_user_id
ON public.template_run_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_template_run_logs_template_id
ON public.template_run_logs(template_id);

CREATE INDEX IF NOT EXISTS idx_template_run_logs_created_at
ON public.template_run_logs(created_at DESC);


-- ============================================================
-- 4. updated_at trigger
-- ============================================================

CREATE OR REPLACE FUNCTION public.set_mental_health_templates_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_mental_health_templates_updated_at
ON public.mental_health_templates;

CREATE TRIGGER trg_mental_health_templates_updated_at
BEFORE UPDATE ON public.mental_health_templates
FOR EACH ROW
EXECUTE FUNCTION public.set_mental_health_templates_updated_at();


-- ============================================================
-- 5. Increment template usage function
-- ============================================================

CREATE OR REPLACE FUNCTION public.increment_template_usage(template_uuid UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE public.mental_health_templates
    SET usage_count = usage_count + 1,
        updated_at = NOW()
    WHERE id = template_uuid;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- 6. Row Level Security
-- ============================================================

ALTER TABLE public.mental_health_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.template_run_logs ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- RLS: mental_health_templates
-- ============================================================

DROP POLICY IF EXISTS "templates_owner_select"
ON public.mental_health_templates;

CREATE POLICY "templates_owner_select"
ON public.mental_health_templates
FOR SELECT
USING (auth.uid() = user_id);


DROP POLICY IF EXISTS "templates_owner_insert"
ON public.mental_health_templates;

CREATE POLICY "templates_owner_insert"
ON public.mental_health_templates
FOR INSERT
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "templates_owner_update"
ON public.mental_health_templates;

CREATE POLICY "templates_owner_update"
ON public.mental_health_templates
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "templates_owner_delete"
ON public.mental_health_templates;

CREATE POLICY "templates_owner_delete"
ON public.mental_health_templates
FOR DELETE
USING (auth.uid() = user_id);


-- ============================================================
-- RLS: research_chat_history
-- ============================================================

DROP POLICY IF EXISTS "research_history_owner_select"
ON public.research_chat_history;

CREATE POLICY "research_history_owner_select"
ON public.research_chat_history
FOR SELECT
USING (auth.uid() = user_id);


DROP POLICY IF EXISTS "research_history_owner_insert"
ON public.research_chat_history;

CREATE POLICY "research_history_owner_insert"
ON public.research_chat_history
FOR INSERT
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "research_history_owner_delete"
ON public.research_chat_history;

CREATE POLICY "research_history_owner_delete"
ON public.research_chat_history
FOR DELETE
USING (auth.uid() = user_id);


-- ============================================================
-- RLS: template_run_logs
-- ============================================================

DROP POLICY IF EXISTS "template_logs_owner_select"
ON public.template_run_logs;

CREATE POLICY "template_logs_owner_select"
ON public.template_run_logs
FOR SELECT
USING (auth.uid() = user_id);


DROP POLICY IF EXISTS "template_logs_owner_insert"
ON public.template_run_logs;

CREATE POLICY "template_logs_owner_insert"
ON public.template_run_logs
FOR INSERT
WITH CHECK (auth.uid() = user_id);


DROP POLICY IF EXISTS "template_logs_owner_delete"
ON public.template_run_logs;

CREATE POLICY "template_logs_owner_delete"
ON public.template_run_logs
FOR DELETE
USING (auth.uid() = user_id);