<script setup lang="ts">
import { reactive, ref } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import type { LandmarkCreateIn } from '@/types';

// 单向初始化：组件挂载时从 initial 拷贝一份内部状态，仅在提交时回传，
// 避免与父组件做双向同步产生回环。父组件用 v-if 控制重新挂载以刷新初值。
const props = defineProps<{
  initial: LandmarkCreateIn;
  loading?: boolean;
  submitText?: string;
}>();

const emit = defineEmits<{
  submit: [LandmarkCreateIn];
}>();

const formRef = ref<FormInstance>();
const form = reactive<LandmarkCreateIn>({
  name: props.initial.name ?? '',
  category: props.initial.category ?? '',
  description: props.initial.description ?? '',
  image_url: props.initial.image_url ?? '',
  lng: props.initial.lng,
  lat: props.initial.lat,
});

const rules: FormRules<LandmarkCreateIn> = {
  name: [
    { required: true, message: '请输入名称', trigger: 'blur' },
    { min: 1, max: 64, message: '1–64 字符', trigger: 'blur' },
  ],
  category: [{ required: true, message: '请输入类别', trigger: 'blur' }],
  lng: [
    { required: true, message: '请输入经度', trigger: 'blur' },
    { type: 'number', min: -180, max: 180, message: '经度范围 -180 ~ 180', trigger: 'blur' },
  ],
  lat: [
    { required: true, message: '请输入纬度', trigger: 'blur' },
    { type: 'number', min: -85.05, max: 85.05, message: '纬度范围 -85.05 ~ 85.05', trigger: 'blur' },
  ],
};

async function onSubmit() {
  if (!formRef.value) return;
  await formRef.value.validate((valid) => {
    if (valid) emit('submit', { ...form });
  });
}

defineExpose({ submit: onSubmit });
</script>

<template>
  <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
    <el-form-item label="名称" prop="name">
      <el-input v-model="form.name" maxlength="64" show-word-limit />
    </el-form-item>
    <el-form-item label="类别" prop="category">
      <el-input v-model="form.category" placeholder="如 history / park / restaurant" />
    </el-form-item>
    <el-form-item label="描述">
      <el-input v-model="form.description" type="textarea" :rows="3" maxlength="500" show-word-limit />
    </el-form-item>
    <el-form-item label="图片 URL">
      <el-input v-model="form.image_url" placeholder="https://..." />
    </el-form-item>
    <div class="coord-row">
      <el-form-item label="经度" prop="lng">
        <el-input-number
          v-model="form.lng"
          :min="-180"
          :max="180"
          :step="0.000001"
          :precision="6"
          controls-position="right"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="纬度" prop="lat">
        <el-input-number
          v-model="form.lat"
          :min="-85.05"
          :max="85.05"
          :step="0.000001"
          :precision="6"
          controls-position="right"
          style="width: 100%"
        />
      </el-form-item>
    </div>
    <el-button type="primary" :loading="loading" class="submit" @click="onSubmit">
      {{ submitText || '保存' }}
    </el-button>
  </el-form>
</template>

<style scoped>
.coord-row {
  display: flex;
  gap: 16px;
}
.coord-row > * {
  flex: 1;
}
.submit {
  width: 100%;
}
</style>
