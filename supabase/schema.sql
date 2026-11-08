-- TrabajoAI schema v1
-- Run in the SQL editor of the intended Supabase project.
create extension if not exists pgcrypto;

create table if not exists public.job_listings (
 id text primary key,
 source text not null default 'external',
 company text not null,
 title text not null,
 location text,
 description text,
 url text not null,
 posted_at timestamptz,
 first_seen_at timestamptz not null default now(),
 last_seen_at timestamptz not null default now(),
 score int check (score between 0 and 100),
 work_type text,
 salary_text text,
 verification text,
 metadata jsonb not null default '{}'::jsonb
);
create index if not exists job_listings_score_idx on public.job_listings(score desc);
create index if not exists job_listings_seen_idx on public.job_listings(last_seen_at desc);

create table if not exists public.candidate_profiles (
 user_id uuid primary key references auth.users(id) on delete cascade,
 master_cv_text text not null default '',
 profile_json jsonb not null default '{}'::jsonb,
 updated_at timestamptz not null default now()
);
create table if not exists public.job_decisions (
 user_id uuid not null references auth.users(id) on delete cascade,
 job_id text not null references public.job_listings(id) on delete cascade,
 status text not null default 'review' check (status in ('review','approved','rejected','applied','interview','offer')),
 notes text,
 updated_at timestamptz not null default now(),
 primary key (user_id, job_id)
);
create table if not exists public.cv_variants (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 job_id text references public.job_listings(id),
 cv_text text not null,
 language text not null default 'es',
 created_at timestamptz not null default now()
);
alter table public.job_listings enable row level security;
alter table public.candidate_profiles enable row level security;
alter table public.job_decisions enable row level security;
alter table public.cv_variants enable row level security;

-- Job listings are public metadata only (no candidate data).
drop policy if exists "Read public job listings" on public.job_listings;
create policy "Read public job listings" on public.job_listings for select using (true);

drop policy if exists "Own candidate profile" on public.candidate_profiles;
create policy "Own candidate profile" on public.candidate_profiles
 for all to authenticated using ((select auth.uid()) = user_id)
 with check ((select auth.uid()) = user_id);
drop policy if exists "Own job decisions" on public.job_decisions;
create policy "Own job decisions" on public.job_decisions
 for all to authenticated using ((select auth.uid()) = user_id)
 with check ((select auth.uid()) = user_id);
drop policy if exists "Own CV variants" on public.cv_variants;
create policy "Own CV variants" on public.cv_variants
 for all to authenticated using ((select auth.uid()) = user_id)
 with check ((select auth.uid()) = user_id);
-- Never expose a service_role key in browser JavaScript or GitHub files.
