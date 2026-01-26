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
Producer labels
*/}}
{{- define "apigw-poc.producer.labels" -}}
app: {{ .Values.producer.name }}
{{ include "apigw-poc.labels" . }}
{{- end }}

{{/*
Consumer labels
*/}}
{{- define "apigw-poc.consumer.labels" -}}
app: {{ .Values.consumer.name }}
{{ include "apigw-poc.labels" . }}
{{- end }}

{{/*
Kong labels
*/}}
{{- define "apigw-poc.kong.labels" -}}
app: {{ .Values.kong.name }}
{{ include "apigw-poc.labels" . }}
{{- end }}
