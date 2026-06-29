create table if not exists public.articles (
  id text primary key,
  title text not null,
  summary text not null,
  category text not null,
  source text,
  url text not null,
  provider text not null,
  raw_summary text,
  importance_score integer not null default 50,
  published_at timestamptz not null,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists articles_published_at_idx
  on public.articles (published_at desc);

create index if not exists articles_category_idx
  on public.articles (category);

alter table public.articles enable row level security;

drop policy if exists "Public can read articles" on public.articles;
create policy "Public can read articles"
  on public.articles
  for select
  to anon
  using (true);

grant usage on schema public to anon;
grant select on public.articles to anon;
