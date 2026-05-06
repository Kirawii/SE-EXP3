<script setup lang="ts">
import { reactive, ref, watch } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import type { LandmarkCreateIn } from '@/types';

const props = defineProps<{
  modelValue: LandmarkCreateIn;
  loading?: boolean;
  submitText?: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [LandmarkCreateIn];
  submit: [LandmarkCreateIn];
}>();

const formRef = ref<FormInstance>();
const form = reactive<LandmarkCreateIn>({ ...props.modelValue });

watch(
  () => props.modelValue,
  (v) => Object.assign(form, v),
  { deep: true },
);

watch(
  form,
  (v) => emit('update:modelValue', { ...v }),
  { deep: true },
);

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
  <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="onSubmit">
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
        <el-input-number v-model="form.lng" :min="-180" :max="180" :step="0.001" :precision="6" />
      </el-form-item>
      <el-form-item label="纬度" prop="lat">
        <el-input-number v-model="form.lat" :min="-85.05" :max="85.05" :step="0.001" :precision="6" />
      </el-form-item>
    </div>
    <el-button type="primary" native-type="submit" :loading="loading" class="submit">
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
