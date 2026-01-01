class PixelArtConverter {
    constructor() {
        this.fileInput = document.getElementById('fileInput');
        this.uploadArea = document.getElementById('uploadArea');
        this.controlsSection = document.getElementById('controlsSection');
        this.previewSection = document.getElementById('previewSection');
        this.loading = document.getElementById('loading');
        
        this.pixelSize = document.getElementById('pixelSize');
        this.method = document.getElementById('method');
        this.numColors = document.getElementById('numColors');
        this.dither = document.getElementById('dither');
        
        this.pixelSizeValue = document.getElementById('pixelSizeValue');
        this.numColorsValue = document.getElementById('numColorsValue');
        
        this.processBtn = document.getElementById('processBtn');
        this.resetBtn = document.getElementById('resetBtn');
        
        this.originalPreview = document.getElementById('originalPreview');
        this.processedPreview = document.getElementById('processedPreview');
        this.downloadLink = document.getElementById('downloadLink');
        
        this.currentFile = null;
        this.initEventListeners();
    }
    
    initEventListeners() {
        // 文件上传事件
        this.uploadArea.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // 拖拽上传事件
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        
        // 参数调节事件
        this.pixelSize.addEventListener('input', () => {
            this.pixelSizeValue.textContent = this.pixelSize.value;
        });
        
        this.numColors.addEventListener('input', () => {
            this.numColorsValue.textContent = this.numColors.value;
        });
        
        // 按钮事件
        this.processBtn.addEventListener('click', () => this.processImage());
        this.resetBtn.addEventListener('click', () => this.reset());
    }
    
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) this.handleFile(file);
    }
    
    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.classList.add('drag-over');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('drag-over');
    }
    
    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFile(files[0]);
        }
    }
    
    handleFile(file) {
        // 验证文件类型
        if (!file.type.startsWith('image/')) {
            alert('请选择图片文件！');
            return;
        }
        
        // 验证文件大小 (限制10MB)
        if (file.size > 10 * 1024 * 1024) {
            alert('文件大小不能超过10MB！');
            return;
        }
        
        this.currentFile = file;
        this.showControls();
        this.showOriginalPreview(file);
    }
    
    showControls() {
        this.controlsSection.style.display = 'block';
        this.uploadArea.style.display = 'none';
    }
    
    showOriginalPreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            this.originalPreview.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
    
    async processImage() {
        if (!this.currentFile) {
            alert('请先选择图片！');
            return;
        }
        
        try {
            this.showLoading();
            
            const formData = new FormData();
            formData.append('file', this.currentFile);
            formData.append('pixel_size', this.pixelSize.value);
            formData.append('method', this.method.value);
            formData.append('num_colors', this.numColors.value);
            formData.append('dither', this.dither.checked);
            
            const response = await fetch('/api/pixelate', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showResult(result);
            } else {
                throw new Error(result.detail || '处理失败');
            }
            
        } catch (error) {
            console.error('处理失败:', error);
            alert('处理失败: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    showResult(result) {
        this.previewSection.style.display = 'block';
        this.processedPreview.src = result.output_url;
        this.downloadLink.href = result.output_url;
        this.downloadLink.download = result.filename;
        
        // 滚动到结果区域
        this.previewSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    showLoading() {
        this.loading.style.display = 'flex';
    }
    
    hideLoading() {
        this.loading.style.display = 'none';
    }
    
    reset() {
        this.currentFile = null;
        this.controlsSection.style.display = 'none';
        this.previewSection.style.display = 'none';
        this.uploadArea.style.display = 'block';
        this.fileInput.value = '';
        
        // 重置参数
        this.pixelSize.value = 8;
        this.method.value = 'average';
        this.numColors.value = 16;
        this.dither.checked = false;
        
        this.pixelSizeValue.textContent = '8';
        this.numColorsValue.textContent = '16';
        
        this.originalPreview.src = '';
        this.processedPreview.src = '';
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new PixelArtConverter();
});