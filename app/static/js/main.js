// 东信光电排产工具 JavaScript 文件

// 通用函数
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 日期格式化函数
function formatDate(date) {
    var d = new Date(date);
    var month = '' + (d.getMonth() + 1);
    var day = '' + d.getDate();
    var year = d.getFullYear();

    if (month.length < 2) month = '0' + month;
    if (day.length < 2) day = '0' + day;

    return [year, month, day].join('-');
}

// 产品规格计算函数
function calculateNestingCount(thickness) {
    // 计算叠数：8微米*(叠数+1) + 产品板厚(微米)*叠数 + 0.8mm ≤ 1.3mm
    // 其中8微米=0.008mm，产品板厚单位是微米需要转换为毫米
    // 公式推导：
    // 0.008*(n+1) + (thickness/1000)*n + 0.8 ≤ 1.3
    // 0.008*n + 0.008 + (thickness/1000)*n + 0.8 ≤ 1.3
    // n*(0.008 + thickness/1000) ≤ 1.3 - 0.808
    var maxN = (1.3 - 0.808) / (0.008 + thickness/1000);
    return Math.floor(maxN) >= 1 ? Math.floor(maxN) : 1;
}

function calculateCuttingCount(length, width, rawGlassSize) {
    if (!rawGlassSize || rawGlassSize.indexOf('x') === -1) {
        return 1; // 默认值
    }

    try {
        var rawParts = rawGlassSize.split('x');
        if (rawParts.length < 2) {
            return 1;
        }

        // 解析原玻尺寸（单位是毫米mm）
        var rawLength = parseFloat(rawParts[0]);  // 单位已经是毫米
        var rawWidth = parseFloat(rawParts[1]);   // 单位已经是毫米

        // 应用点胶偏移：单边4mm，所以每边减去4mm，总共长宽各减去8mm
        var effectiveLength = rawLength - 8;  // 有效长度 = 原玻长度 - 8mm
        var effectiveWidth = rawWidth - 8;    // 有效宽度 = 原玻宽度 - 8mm

        // 确保有效区域为正数
        if (effectiveLength <= 0 || effectiveWidth <= 0) {
            return 1; // 如果有效区域为负或零，则返回默认值1
        }

        // 考虑产品长宽单边+2mm
        var productLengthWithMargin = length + 2 * 2;  // 长度单边+2mm，总共+4mm
        var productWidthWithMargin = width + 2 * 2;    // 宽度单边+2mm，总共+4mm

        // 定义两个方向的产品尺寸
        var orientation1 = [productLengthWithMargin, productWidthWithMargin];  // 原始方向
        var orientation2 = [productWidthWithMargin, productLengthWithMargin];  // 旋转90度

        var maxCount = 1;  // 默认值

        // 尝试不同的布局策略
        for (var i = 0; i < 2; i++) {
            var prodLen = i === 0 ? orientation1[0] : orientation2[0];
            var prodWid = i === 0 ? orientation1[1] : orientation2[1];

            if (prodLen <= effectiveLength && prodWid <= effectiveWidth) {
                // 计算在给定方向下单个方向最多能放多少个产品
                var countAlongX = Math.floor(effectiveLength / prodLen);
                var countAlongY = Math.floor(effectiveWidth / prodWid);

                // 基础排列：全部按同一方向
                var basicCount = countAlongX * countAlongY;
                maxCount = Math.max(maxCount, basicCount);

                // 尝试混合排列，利用剩余空间
                var remainingX = effectiveLength - (countAlongX * prodLen);
                var remainingY = effectiveWidth - (countAlongY * prodWid);

                // 在X方向剩余空间尝试放置旋转的产品
                if (remainingX >= prodWid && prodLen <= effectiveWidth) {
                    var additionalCountX = Math.floor(remainingX / prodWid) * countAlongY;
                    maxCount = Math.max(maxCount, basicCount + additionalCountX);
                }

                // 在Y方向剩余空间尝试放置旋转的产品
                if (remainingY >= prodLen && prodWid <= effectiveLength) {
                    var additionalCountY = Math.floor(remainingY / prodLen) * countAlongX;
                    maxCount = Math.max(maxCount, basicCount + additionalCountY);
                }
            }
        }

        return Math.max(maxCount, 1);
    } catch (e) {
        return 1; // 如果解析失败，返回默认值
    }
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 添加表单验证
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // 检查必填字段
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('请填写所有必填字段');
            }
        });
    });
    
    // 在订单创建/编辑页面添加实时计算功能
    const createOrderForm = document.querySelector('#create-order-form, form[action*="order/create"], form[action*="order/edit"]');
    if (createOrderForm) {
        const lengthInput = document.getElementById('length');
        const widthInput = document.getElementById('width');
        const thicknessInput = document.getElementById('thickness');
        const rawGlassSizeInput = document.getElementById('raw_glass_size');
        
        if (lengthInput && widthInput && thicknessInput && rawGlassSizeInput) {
            // 为输入字段添加事件监听器
            [lengthInput, widthInput, thicknessInput, rawGlassSizeInput].forEach(input => {
                input.addEventListener('input', updateCalculatedFields);
            });
            
            // 初始化计算
            updateCalculatedFields();
        }
    }
});

function updateCalculatedFields() {
    const lengthInput = document.getElementById('length');
    const widthInput = document.getElementById('width');
    const thicknessInput = document.getElementById('thickness');
    const rawGlassSizeInput = document.getElementById('raw_glass_size');
    
    if (lengthInput && widthInput && thicknessInput && rawGlassSizeInput) {
        const length = parseFloat(lengthInput.value) || 0;
        const width = parseFloat(widthInput.value) || 0;
        const thickness = parseFloat(thicknessInput.value) || 0;
        const rawGlassSize = rawGlassSizeInput.value;
        
        // 计算叠数
        const nestingCount = calculateNestingCount(thickness);
        
        // 计算切数
        const cuttingCount = calculateCuttingCount(length, width, rawGlassSize);
        
        // 更新UI显示（如果存在显示元素）
        const nestingDisplay = document.getElementById('nesting-display');
        const cuttingDisplay = document.getElementById('cutting-display');
        
        if (nestingDisplay) {
            nestingDisplay.textContent = nestingCount;
        }
        
        if (cuttingDisplay) {
            cuttingDisplay.textContent = cuttingCount;
        }
    }
}

// 为模态框添加关闭事件处理
document.addEventListener('DOMContentLoaded', function() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function() {
            // 清空模态框中的表单数据
            const form = modal.querySelector('form');
            if (form) {
                form.reset();
            }
        });
    });
});