interface ModelBoxProps {
  modelList: {
    model_name: string;
    provider: string;
    parameters: string;
    isNew: boolean;
    background: string;
  }[];
}

export type { ModelBoxProps };
