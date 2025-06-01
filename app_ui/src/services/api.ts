import axios from 'axios';

const API_URL = 'https://fitify-07vt.onrender.com';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface OutfitSuggestionParams {
  location: string;
  formality: string;
  activity: string;
  available_items?: string;
}

export interface OutfitLog {
  outfit_id: string;
  items: string[];
  date_worn: string;
  weather: {
    temperature: number;
    conditions: string;
  };
  activity: string;
  formality: string;
  notes?: string;
}

export interface ClothingItem {
  id: string;
  type: string;
  form: string;
  weather: string[];
  color: string;
  notes: string;
  count: number;
  image: string;
}

export const apiService = {
  getOutfitSuggestion: async (params: OutfitSuggestionParams) => {
    try {
      const response = await api.get('/suggest_outfit', { params });
      return response.data;
    } catch (error) {
      console.error('Error getting outfit suggestion:', error);
      throw error;
    }
  },

  logOutfit: async (outfit: OutfitLog) => {
    try {
      const response = await api.post('/log_outfit', outfit);
      return response.data;
    } catch (error) {
      console.error('Error logging outfit:', error);
      throw error;
    }
  },

  getOutfitHistory: async () => {
    try {
      const response = await api.get('/outfit_history');
      return response.data;
    } catch (error) {
      console.error('Error getting outfit history:', error);
      throw error;
    }
  },

  addItem: async (item: any) => {
    try {
      const response = await api.post('/add_item', item);
      return response.data;
    } catch (error) {
      console.error('Error adding item:', error);
      throw error;
    }
  },

  removeItem: async (itemId: string) => {
    try {
      const response = await api.delete(`/remove_item/${itemId}`);
      return response.data;
    } catch (error) {
      console.error('Error removing item:', error);
      throw error;
    }
  },

  getWardrobe: async () => {
    try {
      const response = await api.get('/wardrobe');
      return response.data;
    } catch (error) {
      console.error('Error getting wardrobe:', error);
      throw error;
    }
  },

  identifyClothing: async (imageUri: string): Promise<ClothingItem> => {
    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', {
        uri: imageUri,
        type: 'image/png',
        name: 'clothing.png',
      } as any);

      // Make the request with the correct content type
      const response = await axios.post(`${API_URL}/identify_clothing`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response.data;
    } catch (error) {
      console.error('Error identifying clothing:', error);
      throw error;
    }
  },
}; 