-- CoalMind tables on the existing Supabase project.
-- Service role bypasses RLS; anon has no policies.

create table if not exists public.documents (
    id text primary key,
    filename text not null,
    file_type text not null,
    status text not null default 'uploaded',
    upload_timestamp timestamptz not null default now(),
    file_path text not null default '',
    sha256 text,
    size_bytes integer default 0,
    confidence_score double precision default 0.98,
    compliance_status text default 'DGMS-COMPLIANT',
    pages_count integer default 1
);

create table if not exists public.document_chunks (
    id bigint generated always as identity primary key,
    document_id text not null references public.documents(id) on delete cascade,
    document_name text not null,
    chunk_index integer not null default 0,
    page_number integer not null default 1,
    text text not null,
    bounding_box jsonb not null default '[0,0,0,0]'::jsonb,
    embedding jsonb
);

create table if not exists public.metrics (
    id bigint generated always as identity primary key,
    document_id text not null references public.documents(id) on delete cascade,
    subsidiary text,
    mine text,
    year text,
    parameter text,
    value double precision,
    unit text,
    page_number integer,
    source_doc text
);

create table if not exists public.conflicts (
    id bigint generated always as identity primary key,
    subsidiary text,
    mine text,
    year text,
    parameter text,
    val1 double precision,
    source1 text,
    val2 double precision,
    source2 text,
    discrepancy_pct double precision,
    statutory_impact text,
    reconciliation_status text,
    detected_at timestamptz not null default now()
);

create table if not exists public.audit_logs (
    id bigint generated always as identity primary key,
    timestamp timestamptz not null default now(),
    event_type text not null,
    operator text not null,
    details text not null,
    integrity_hash text not null
);

create index if not exists document_chunks_document_id_idx on public.document_chunks (document_id);
create index if not exists metrics_scope_idx on public.metrics (subsidiary, mine, year, parameter);

alter table public.documents enable row level security;
alter table public.document_chunks enable row level security;
alter table public.metrics enable row level security;
alter table public.conflicts enable row level security;
alter table public.audit_logs enable row level security;
