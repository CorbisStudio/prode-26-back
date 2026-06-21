# Deploy — prode-back

Despliegue automático a **mark1** (MicroK8s) en cada push a `master`.

## Cómo funciona
1. Push a `master` → GitHub Actions corre el workflow `.github/workflows/deploy_mark1_master.yml`
   en un **self-hosted runner** sobre mark1.
2. El runner buildea la imagen, la pushea al registry local (`localhost:32000`) con tag
   inmutable `master-<sha>` y hace rollout de **web + worker + beat**.
3. Si cambian archivos en `*/migrations/`, corre un Job de `migrate` antes de terminar.

## Manual
```bash
# desde mark1
cd ~/workspaces/corbis/repos/prode-back && bash scripts/deploy-mark1.sh prod
```

## Verificación
```bash
microk8s kubectl -n prode-prod get pods
microk8s kubectl -n prode-prod get certificate
```

- URL: https://prode.vera-demo.site
- Namespace: `prode-prod`
- Scoring nocturno (Celery beat): 02:00 (hora Argentina)
