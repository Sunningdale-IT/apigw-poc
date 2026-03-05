# PostgreSQL Persistence Test

This document shows how to test that PostgreSQL data persists across Helm uninstall/reinstall.

## Test Procedure

### 1. Install the Helm chart
```bash
helm install apigw-demo . -f secrets.yaml -n apigw-demo
```

### 2. Wait for PostgreSQL to be ready
```bash
kubectl wait --for=condition=ready pod/apigw-demo-postgres-0 -n apigw-demo --timeout=300s
```

### 3. Create test data
```bash
# Connect to PostgreSQL and create a test table with data
kubectl exec -it apigw-demo-postgres-0 -n apigw-demo -- psql -U postgres -d dogcatcher -c "
CREATE TABLE IF NOT EXISTS persistence_test (
  id SERIAL PRIMARY KEY,
  test_data VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO persistence_test (test_data) VALUES 
  ('Test entry 1 - before uninstall'),
  ('Test entry 2 - before uninstall');
"

# Verify data was created
kubectl exec -it apigw-demo-postgres-0 -n apigw-demo -- pkubectl exec -it apigw-demo-postgres-0 -n apigw-demo -- pkubectl exec -it apigw-demo-postgres-0 -n apie
kubectl exec -it apigw-demo--dekubectl exec -it apigw### 5. Verify PVC still exists
```bash
kubectl get pvc -n apigw-demo
# Sho# Sho# Sho# Sho#es-# Sho# Sho# Sho# Sho#es-# Shkubectl de# Sho# Sho# Sho# Sho#es-# Sho# Sho# Sho# Sho#es-# Shkuw-# mo
# Sho# Sho# Sho# Sho#es-# Sho# Sho# Smi# Sho#)
# Sho# Sho# Sho# Sho#es-# Sho# Sho# Smi# Sho#)
-# Shkubectl de# Sho# Sho# Sho# Sho#es-#  --#sec-# Shkubectl de# Sho# o
-# Shk##-# Shk##-# Shk##-# Shk##-# Shk##-# Shk##-# Shk##-# Shk##l -# Shk##-# Shk##-# Shk##-# Shk##-# Shk##-# Shk##-# Shk##-# Shk##l -# Shk##-# Shk##-# Shk## 8-# Shk##-# Shk##-# Shk##-# Shk##-# Shk##-# Sur-# Shk##-# Shk##-# Shk#
kkkkkkkkkkkkkkkkkkkkkkkkkmokkkkkkkkkkkkkkkkkkkkkkkkkmokkkkkkkkU kostkkkkkkkkkkkkkkkkkkkkkkkkkmokkkkkkkkkkkkkkkkkkkkce_test;
"

# Expected output: Both test # Expected output: Both test # Expect## 9.# Expected output: Both m # Expected output: Both test # Expected output: Both test # Expect## 9.# Expected output: Both m # Expected output: Both test # Expected output: Both test # Exta# Expected output: Both test # Expected output: Both test # Expect## 9.# Expected Ex# Expe output: All 3 entries should be visible
```

## Expected Results

✅ **SUCCESS**: If you see all 3 test entries after reinstall
❌ **FAILURE**: If the t❌ **FAILURE**: If the t❌ **FAILURE**: If y
❌ **FAILURE**: If the t❌ **FAILURE**: If ve the persistent data:

```bash
# Uninstall release
helm uninstall apigw-helm uninstall apigw-helm uninstall apigw-helm uninstall apigw-helm uninstall apigw-helm uninstall apigw-helm uninstall apigw-helm uninstall apigw-helm uninstall apigw-helm uninstall apigw-helm uninstall apigw-helm uninstall amlhelm uninstall apigw-helm uninstall apigw-helm uninstall apigw-helm uninstall apigw-helm uninstall apigw-helm uninstall apd ordinal (postgres-0)
- **Storage class**: The PVC uses the storage class specified in values.yaml
- **Backup strategy**: For production, implement regular backups using `pg_dump` or automated backup solutions

