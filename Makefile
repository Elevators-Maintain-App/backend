deploy:
	@echo "Iniciando el despliegue en Cloud Run GCP..."
	@chmod +x deploy.sh
	@./deploy.sh && \
	echo "\033[32m✅ Despliegue exitoso.\033[0m" || \
	(echo "\033[31m❌ Error durante el despliegue.\033[0m" && exit 1)
