{{/*
Expand the name of the chart.
*/}}
{{- define "apigw-poc.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "apigw-poc.fullname" -}}
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
{{- define "apigw-poc.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "apigw-poc.labels" -}}
helm.sh/chart: {{ include "apigw-poc.chart" . }}
{{ include "apigw-poc.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "apigw-poc.selectorLabels" -}}
app.kubernetes.io/name: {{ include "apigw-poc.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "apigw-poc.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "apigw-poc.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Kong labels
*/}}
{{- define "apigw-poc.kong.labels" -}}
helm.sh/chart: {{ include "apigw-poc.chart" . }}
{{ include "apigw-poc.kong.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: kong
{{- end }}

{{- define "apigw-poc.kong.selectorLabels" -}}
app.kubernetes.io/name: {{ include "apigw-poc.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: kong
{{- end }}

{{/*
Kong Keycloak Authentication Helpers
*/}}
{{- define "apigw-poc.kong.keycloak.enabledReady" -}}
{{- if and .Values.kong.enabled .Values.kong.keycloakAuth.enabled .Values.kong.keycloakAuth.clientSecret -}}
true
{{- else -}}
false
{{- end -}}
{{- end -}}

{{- define "apigw-poc.kong.keycloak.issuerUrl" -}}
{{- if .Values.kong.keycloakAuth.issuerUrl -}}
{{- .Values.kong.keycloakAuth.issuerUrl -}}
{{- else -}}
https://keycloak.{{ .Values.global.domainSuffix }}/realms/master
{{- end -}}
{{- end -}}
