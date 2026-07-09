SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public' AND tablename = 'GenerationJob'
ORDER BY indexname;
