import { Dimensions } from 'react-native';
import { ColorValue } from 'react-native';

const { width, height } = Dimensions.get('window');

export const theme = {
  colors: {
    primary: '#6C63FF' as ColorValue,
    secondary: '#FF6584' as ColorValue,
    background: '#121212' as ColorValue,
    surface: '#1E1E1E' as ColorValue,
    text: '#FFFFFF' as ColorValue,
    textSecondary: '#B3B3B3' as ColorValue,
    error: '#FF5252' as ColorValue,
    success: '#4CAF50' as ColorValue,
    warning: '#FFC107' as ColorValue,
    card: '#2D2D2D' as ColorValue,
    border: '#3D3D3D' as ColorValue,
  },
  gradients: {
    primary: ['#6C63FF', '#4A45B3'] as [ColorValue, ColorValue],
    secondary: ['#FF6584', '#FF4B6C'] as [ColorValue, ColorValue],
    background: ['#121212', '#1E1E1E'] as [ColorValue, ColorValue],
    card: ['#2D2D2D', '#3D3D3D'] as [ColorValue, ColorValue],
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  typography: {
    h1: {
      fontSize: 32,
      fontWeight: '700' as const,
    },
    h2: {
      fontSize: 24,
      fontWeight: '700' as const,
    },
    h3: {
      fontSize: 20,
      fontWeight: '700' as const,
    },
    body: {
      fontSize: 16,
      fontWeight: '400' as const,
    },
    caption: {
      fontSize: 14,
      color: '#B3B3B3' as ColorValue,
      fontWeight: '400' as const,
    },
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 16,
    xl: 24,
  },
  dimensions: {
    width,
    height,
  },
  shadows: {
    small: {
      shadowColor: '#000',
      shadowOffset: {
        width: 0,
        height: 2,
      },
      shadowOpacity: 0.25,
      shadowRadius: 3.84,
      elevation: 2,
    },
    medium: {
      shadowColor: '#000',
      shadowOffset: {
        width: 0,
        height: 4,
      },
      shadowOpacity: 0.30,
      shadowRadius: 4.65,
      elevation: 4,
    },
    large: {
      shadowColor: '#000',
      shadowOffset: {
        width: 0,
        height: 6,
      },
      shadowOpacity: 0.37,
      shadowRadius: 7.49,
      elevation: 6,
    },
  },
}; 