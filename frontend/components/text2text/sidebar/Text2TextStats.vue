<!--
  - coding=utf-8
  - Copyright 2021-present, the Recognai S.L. team.
  -
  - Licensed under the Apache License, Version 2.0 (the "License");
  - you may not use this file except in compliance with the License.
  - You may obtain a copy of the License at
  -
  -     http://www.apache.org/licenses/LICENSE-2.0
  -
  - Unless required by applicable law or agreed to in writing, software
  - distributed under the License is distributed on an "AS IS" BASIS,
  - WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  - See the License for the specific language governing permissions and
  - limitations under the License.
  -->

<template>
  <div>
    <p class="sidebar__title">Stats</p>
    <StatsSelector
      :selected-option="selectedOption"
      :options="options"
      @selectOption="onSelectOption"
    />
    <template v-if="selectedOption.id === 'keywords'">
      <div class="scroll">
        <div v-for="(counter, keyword) in getKeywords" :key="keyword">
          <div v-if="counter > 0" class="info">
            <label>{{ keyword }}</label>
            <span class="records-number">{{ counter | formatNumber }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
export default {
  // TODO clean and typify
  props: {
    dataset: {
      type: Object,
      required: true,
    },
  },
  data: () => {
    return {
      selectedOption: {
        id: "keywords",
        name: "Keywords",
      },
    };
  },
  computed: {
    getKeywords() {
      const words = this.dataset.results.aggregations.words;
      return Object.fromEntries(
        Object.entries(words).sort((a, b) => b[1] - a[1])
      );
    },
    options() {
      let options = [];
      options.push({
        id: "keywords",
        name: "Keywords",
      });
      return options;
    },
  },
  methods: {
    onSelectOption(opt) {
      this.selectedOption = opt;
    },
  },
};
</script>
<style lang="scss" scoped>
label {
  display: block;
  width: calc(100% - 40px);
  word-break: break-word;
  hyphens: auto;
}
.labels {
  margin-top: 3em;
  strong {
    margin-bottom: 1em;
    display: block;
  }
}
.info {
  position: relative;
  display: flex;
  margin-bottom: 0.7em;
  color: $font-secondary-dark;
}
.scroll {
  max-height: calc(100vh - 200px);
  padding-right: 1em;
  margin-right: -1em;
  overflow: auto;
  @extend %hide-scrollbar;
}
.records-number {
  margin-right: 0;
  margin-left: auto;
}
</style>
