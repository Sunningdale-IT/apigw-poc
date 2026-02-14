{{/*
Expand the name of the chart.
*/}}
{{- define "apigw-demo.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "apigw-demo.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "apigw-demo.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "apigw-demo.labels" -}}
helm.sh/chart: {{ include "apigw-demo.chart" . }}
{{ include "apigw-demo.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "apigw-demo.selectorLabels" -}}
app.kubernetes.io/name: {{ include "apigw-demo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "apigw-demo.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "apigw-demo.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Dogcatcher labels
*/}}
{{- define "apigw-demo.dogcatcher.labels" -}}
helm.sh/chart: {{ include "apigw-demo.chart" . }}
{{ include "apigw-demo.dogcatcher.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: api
{{- end }}

{{- define "apigw-demo.dogcatcher.selectorLabels" -}}
app.kubernetes.io/name: {{ include "apigw-demo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: dogcatcher
{{- end }}

{{/*
Dogcatcher DB labels
*/}}
{{- define "apigw-demo.dogcatcher-db.labels" -}}
helm.sh/chart: {{ include "apigw-demo.chart" . }}
{{ include "apigw-demo.dogcatcher-db.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: database
{{- end }}

{{- define "apigw-demo.dogcatcher-db.selectorLabels" -}}
app.kubernetes.io/name: {{ include "apigw-demo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: dogcatcher-db
{{- end }}

{{/*
Kong labels
*/}}
{{- define "apigw-demo.kong.labels" -}}
helm.sh/chart: {{ include "apigw-demo.chart" . }}
{{ include "apigw-demo.kong.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: gateway
{{- end }}

{{- define "apigw-demo.kong.selectorLabels" -}}
app.kubernetes.io/name: {{ include "apigw-demo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: kong
{{- end }}

{{/*
Kong DB labels
*/}}
{{- define "apigw-demo.kong-db.labels" -}}
helm.sh/chart: {{ include "apigw-demo.chart" . }}
{{ include "apigw-demo.kong-db.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: database
{{- end }}

{{- define "apigw-demo.kong-db.selectorLabels" -}}
app.kubernetes.io/name: {{ include "apigw-demo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: kong-db
{{- end }}

{{/*
Citizen labels
*/}}
{{- define "apigw-demo.citizen.labels" -}}
helm.sh/chart: {{ include "apigw-demo.chart" . }}
{{ include "apigw-demo.citizen.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: portal
{{- end }}

{{- define "apigw-demo.citizen.selectorLabels" -}}
app.kubernetes.io/name: {{ include "apigw-demo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: citizen
{{- end }}

{{/*
Certosaurus labels
*/}}
{{- define "apigw-demo.certosaurus.labels" -}}
helm.sh/chart: {{ include "apigw-demo.chart" . }}
{{ include "apigw-demo.certosaurus.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: certificates
{{- end }}

{{- define "apigw-demo.certosaurus.selectorLabels" -}}
app.kubernetes.io/name: {{ include "apigw-demo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: certosaurus
{{- end }}

{{/*
Keycloak labels
*/}}
{{- define "apigw-demo.keycloak.labels" -}}
helm.sh/chart: {{ include "apigw-demo.chart" . }}
{{ include "apigw-demo.keycloak.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: identity
{{- end }}

{{- define "apigw-demo.keycloak.selectorLabels" -}}
app.kubernetes.io/name: {{ include "apigw-demo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: keycloak
{{- end }}

{{/*
PostgreSQL labels
*/}}
{{- define "apigw-demo.postgres.labels" -}}
helm.sh/chart: {{ include "apigw-demo.chart" . }}
{{ include "apigw-demo.postgres.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: database
{{- end }}

{{- define "apigw-demo.postgres.selectorLabels" -}}
app.kubernetes.io/name: {{ include "apigw-demo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: postgres
{{- end }}

{{/*
Storage class helper
*/}}
{{- define "apigw-demo.storageClass" -}}
{{- if .storageClass }}
{{- if (eq "-" .storageClass) }}
storageClassName: ""
{{- else }}
storageClassName: {{ .storageClass }}
{{- end }}
{{- else if .global }}
{{- if .global.storageClass }}
storageClassName: {{ .global.storageClass }}
{{- end }}
{{- end }}
{{- end }}
