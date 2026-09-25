-- Public read for the GitHub Pages demo. No writes for anon.
grant usage on schema public to anon;
grant select on table public.documents to anon;
grant select on table public.document_chunks to anon;
grant select on table public.metrics to anon;
grant select on table public.conflicts to anon;

drop policy if exists anon_read_documents on public.documents;
create policy anon_read_documents on public.documents for select to anon using (true);

drop policy if exists anon_read_chunks on public.document_chunks;
create policy anon_read_chunks on public.document_chunks for select to anon using (true);

drop policy if exists anon_read_metrics on public.metrics;
create policy anon_read_metrics on public.metrics for select to anon using (true);

drop policy if exists anon_read_conflicts on public.conflicts;
create policy anon_read_conflicts on public.conflicts for select to anon using (true);
