-- Como usar:
-- 1. No Supabase: Database -> Extensions -> ativar "pg_cron" e "pg_net"
-- 2. Trocar SEU-DOMINIO.vercel.app pela URL real do site (depois do deploy)
-- 3. Colar este arquivo inteiro no SQL Editor do Supabase e clicar Run
-- 4. Pronto -- o Supabase passa a chamar o sistema sozinho a cada 5 minutos, para sempre

create extension if not exists pg_cron;
create extension if not exists pg_net;

select cron.schedule(
  'processar-fila-envios',
  '*/5 * * * *',
  $$
  select net.http_get(
    url := 'https://mensageria-cyan.vercel.app/cron/processar-fila/',
    headers := jsonb_build_object('Authorization', 'Bearer XRq3B8KjZoPej2_phDrxUjyfgCxdd1wPc7jICCgAE2Q')
  );
  $$
);

select cron.schedule(
  'processar-importacoes',
  '*/5 * * * *',
  $$
  select net.http_get(
    url := 'https://mensageria-cyan.vercel.app/cron/processar-importacoes/',
    headers := jsonb_build_object('Authorization', 'Bearer XRq3B8KjZoPej2_phDrxUjyfgCxdd1wPc7jICCgAE2Q')
  );
  $$
);

-- Pra conferir se os despertadores estao ativos, rode depois:
-- select * from cron.job;

-- Pra desativar um deles no futuro:
-- select cron.unschedule('processar-fila-envios');
-- select cron.unschedule('processar-importacoes');
