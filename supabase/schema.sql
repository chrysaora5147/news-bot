create table if not exists public.articles (
  id text primary key,
  title text not null,
  title_th text,
  summary text not null,
  summary_th text,
  category text not null,
  source text,
  url text not null,
  image_url text,
  provider text not null,
  raw_summary text,
  story_id text,
  source_count integer not null default 1,
  source_urls jsonb not null default '[]'::jsonb,
  trending_score integer not null default 50,
  line_candidate boolean not null default false,
  line_approved_at timestamptz,
  line_rejected_at timestamptz,
  line_review_note text,
  line_sent_at timestamptz,
  importance_score integer not null default 50,
  published_at timestamptz not null,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists articles_published_at_idx
  on public.articles (published_at desc);

create index if not exists articles_category_idx
  on public.articles (category);

create index if not exists articles_trending_score_idx
  on public.articles (trending_score desc);

create index if not exists articles_line_candidate_idx
  on public.articles (line_candidate, line_sent_at);

create index if not exists articles_line_review_idx
  on public.articles (line_candidate, line_approved_at, line_rejected_at, line_sent_at);

alter table public.articles enable row level security;

drop policy if exists "Public can read articles" on public.articles;
create policy "Public can read articles"
  on public.articles
  for select
  to anon
  using (true);

grant usage on schema public to anon;
grant select on public.articles to anon;
