#!/usr/bin/env python3
"""
Data Visualizer Module
数据可视化模块

This module contains the StaticDataVisualizer class for creating 
comprehensive visualizations of static clinical data analysis.
本模块包含StaticDataVisualizer类，用于创建静态临床数据分析的综合可视化。
"""

import os
import warnings
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import logging

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Configure logging for this module
logger = logging.getLogger(__name__)


class StaticDataVisualizer:
    """
    Static data visualizer for categorical variables in clinical data.
    静态数据可视化器，用于临床数据中的分类变量可视化。
    
    This class provides comprehensive visualization capabilities for static clinical data,
    including grouped variable charts, summary dashboards, and customizable plot layouts.
    """
    
    def __init__(self, config_manager: Any) -> None:
        """
        Initialize the visualizer with configuration.
        使用配置初始化可视化器。
        
        Args:
            config_manager: ConfigManager instance for accessing configuration
        """
        self.config = config_manager
        self.df: Optional[pd.DataFrame] = None
        self.total_patients: int = 0
        
        # Set up matplotlib with configurable parameters
        self._setup_matplotlib_params()
    
    def _setup_matplotlib_params(self) -> None:
        """
        Setup matplotlib configuration based on subplot parameters.
        根据子图参数设置matplotlib配置。
        """
        subplot_params = self.config.get('visualization', 'subplot_params', {})
        font_sizes = self.config.get('display', 'font_sizes', {})
        
        # Set global matplotlib parameters
        plt.rcParams['font.family'] = subplot_params.get('font_family', ['DejaVu Sans'])
        plt.rcParams['font.size'] = subplot_params.get('tick_labelsize', 8)
        plt.rcParams['axes.titlesize'] = subplot_params.get('title_fontsize', 12)
        plt.rcParams['axes.labelsize'] = subplot_params.get('xlabel_fontsize', 10)
        plt.rcParams['xtick.labelsize'] = subplot_params.get('tick_labelsize', 8)
        plt.rcParams['ytick.labelsize'] = subplot_params.get('tick_labelsize', 8)
        plt.rcParams['legend.fontsize'] = font_sizes.get('small', 9)
        plt.rcParams['figure.titlesize'] = font_sizes.get('title', 18)
    
    def load_data(self, df: Optional[pd.DataFrame] = None) -> bool:
        """
        Load data from DataFrame or from configured input file.
        从DataFrame或配置的输入文件加载数据。
        
        Args:
            df: Optional DataFrame to use instead of loading from file
            
        Returns:
            True if data loaded successfully, False otherwise
            
        Raises:
            FileNotFoundError: If input file cannot be found
            pd.errors.EmptyDataError: If input file is empty
        """
        if df is not None:
            self.df = df
            self.total_patients = len(self.df)
            logger.info(f"Data loaded from provided DataFrame. Total patients: {self.total_patients}")
            print(f"Data loaded from provided DataFrame. Total patients: {self.total_patients}")
            return True
        
        input_file = self.config.get_path('input_file')
        try:
            self.df = pd.read_csv(input_file)
            self.total_patients = len(self.df)
            logger.info(f"Successfully loaded data from: {input_file}")
            logger.info(f"Total patients: {self.total_patients}")
            print(f"Successfully loaded data from: {input_file}")
            print(f"Total patients: {self.total_patients}")
            return True
        except FileNotFoundError:
            error_msg = f"Input file not found: {input_file}"
            logger.error(error_msg)
            print(f"Error: {error_msg}")
            return False
        except pd.errors.EmptyDataError:
            error_msg = f"Input file is empty: {input_file}"
            logger.error(error_msg)
            print(f"Error: {error_msg}")
            return False
        except Exception as e:
            error_msg = f"Error reading input file {input_file}: {e}"
            logger.error(error_msg)
            print(f"Error: {error_msg}")
            return False
    
    def create_comprehensive_visualization(self) -> None:
        """
        Create comprehensive visualization of all categorical variables.
        创建所有分类变量的综合可视化。
        """
        if self.df is None:
            print("Error: No data loaded. Call load_data() first.")
            return
        
        print("Creating comprehensive visualization...")
        
        # Get all variables to visualize
        visualization_vars = self.config.get('visualization', 'variables')
        
        # Group variables into sets of 5
        var_groups = [visualization_vars[i:i+5] for i in range(0, len(visualization_vars), 5)]
        
        # Create visualization for each group
        for group_idx, var_group in enumerate(var_groups, 1):
            self._create_group_visualization(var_group, group_idx)
        
        print("Comprehensive visualization completed!")
    
    def _create_group_visualization(self, variables: List[str], group_number: int) -> None:
        """
        Create visualization for a group of variables (max 5).
        
        Args:
            variables: List of variable names to visualize
            group_number: Group number for filename
        """
        # Calculate layout
        num_vars = len(variables)
        
        # Get subplot parameters for dimension calculation
        subplot_params = self.config.get('visualization', 'subplot_params', {})
        individual_width = subplot_params.get('individual_width', 3.0)
        aspect_ratio = subplot_params.get('aspect_ratio', 0.5)
        
        # Calculate figure dimensions based on new specifications
        # Y轴总高度 = X轴宽度 × 2 (aspect_ratio = 0.5 means height/width = 2)
        subplot_width = num_vars * individual_width
        subplot_height = individual_width / aspect_ratio  # height = width / 0.5 = width * 2
        
        # Add extra space for title and adjust total figure height
        title_spacing = subplot_params.get('title_to_subplot_spacing', 0.08)
        fig_height = subplot_height + (subplot_height * title_spacing)
        
        # Create figure with calculated dimensions
        fig = plt.figure(figsize=(subplot_width, fig_height))
        
        # Create main title with improved positioning
        title = f"Clinical Data Analysis - Group {group_number}"
        main_title_fontsize = subplot_params.get('main_title_fontsize', 16)
        main_title_y_position = subplot_params.get('main_title_y_position', 0.98)
        
        fig.suptitle(title, fontsize=main_title_fontsize, fontweight='bold', 
                    y=main_title_y_position)
        
        # Create subplots with specific positioning and improved spacing
        for i, var in enumerate(variables):
            if var in self.df.columns:
                # Calculate position (1 row, up to 5 columns)
                ax = fig.add_subplot(1, num_vars, i + 1)
                self._create_single_variable_plot(ax, var)
            else:
                print(f"Warning: Variable '{var}' not found in data")
        
        # Adjust layout with calculated margins to maintain subplot proportions
        subplot_area_top = subplot_params.get('subplot_area_top', 0.90)
        bottom_margin = self.config.get('visualization', 'bottom_margin', 0.08)
        left_margin = self.config.get('visualization', 'left_margin', 0.08)
        right_margin = self.config.get('visualization', 'right_margin', 0.95)
        wspace = self.config.get('visualization', 'wspace', 0.3)
        hspace = self.config.get('visualization', 'hspace', 0.4)
        
        plt.subplots_adjust(
            top=subplot_area_top,  # Use calculated top margin for subplot area
            bottom=bottom_margin,
            left=left_margin,
            right=right_margin,
            wspace=wspace,
            hspace=hspace
        )
        
        # Save figure
        self._save_figure(fig, f"comprehensive_analysis_group_{group_number}")
        plt.close(fig)
    
    def _create_single_variable_plot(self, ax, variable: str) -> None:
        """
        Create a single variable plot with configurable parameters.
        
        Args:
            ax: Matplotlib axis
            variable: Variable name to plot
        """
        # Get subplot parameters
        subplot_params = self.config.get('visualization', 'subplot_params', {})
        
        # Get data for the variable
        data = self.df[variable].dropna()
        
        if len(data) == 0:
            ax.text(0.5, 0.5, f'No data\nfor {variable}', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, 
                   fontsize=subplot_params.get('xlabel_fontsize', 10),
                   color=subplot_params.get('text_color', 'black'))
            self._apply_subplot_styling(ax, variable, subplot_params)
            return
        
        # Special handling for Age variable - convert to categorical
        if variable == "Age":
            data = self._process_age_data(data)
        
        # Special handling for toxicity grade variables - convert to categorical integers
        toxicity_vars = ["CRS grade", "ICANS grade", "Early ICAHT grade", "Late ICAHT grade", "Infection grade"]
        if variable in toxicity_vars:
            data = self._process_toxicity_grade_data(data)
        
        # Special handling for extranodal involvement - ensure categorical
        if variable == "extranodal involvement":
            data = self._process_extranodal_data(data)
        
        # Always treat as categorical data for consistency
        self._create_bar_chart(ax, data, variable, subplot_params)
        
        # Apply general subplot styling
        self._apply_subplot_styling(ax, variable, subplot_params)
    
    def _process_age_data(self, data: pd.Series) -> pd.Series:
        """
        Process age data into categorical groups based on config threshold.
        
        Args:
            data: Age data series
            
        Returns:
            Categorical age groups
        """
        age_threshold = self.config.get('analysis', 'age_threshold', 65)
        
        def categorize_age(age):
            if age < age_threshold:
                return f"< {age_threshold}岁"
            else:
                return f"≥ {age_threshold}岁"
        
        return data.apply(categorize_age)
    
    def _process_toxicity_grade_data(self, data: pd.Series) -> pd.Series:
        """
        Process toxicity grade data to ensure integer categorical values.
        
        Args:
            data: Toxicity grade data series
            
        Returns:
            Integer categorical toxicity grades
        """
        # Convert any float values to integers
        processed_data = data.apply(lambda x: int(round(x)) if pd.notnull(x) else x)
        return processed_data
    
    def _process_extranodal_data(self, data: pd.Series) -> pd.Series:
        """
        Process extranodal involvement data to ensure categorical values (0, 1, 2).
        
        Args:
            data: Extranodal involvement data series
            
        Returns:
            Categorical extranodal involvement data
        """
        # Ensure values are treated as categorical integers
        processed_data = data.apply(lambda x: str(int(x)) if pd.notnull(x) else x)
        return processed_data
    
    def _apply_subplot_styling(self, ax, variable: str, subplot_params: Dict) -> None:
        """Apply consistent styling to subplot with improved title positioning."""
        # Set title (only if enabled in config) - positioned at bottom with consistent spacing
        if subplot_params.get('show_subplot_titles', True):
            title_fontsize = subplot_params.get('title_fontsize', 12)
            title_fontweight = subplot_params.get('title_fontweight', 'bold')
            title_pad = subplot_params.get('title_pad', 15)  # 增加间距以确保一致性
            text_color = subplot_params.get('text_color', 'black')
            
            # Apply display name mapping for visualization titles
            display_name = self._get_display_name(variable)
            
            # Move title to bottom as xlabel instead of top title with improved spacing
            ax.set_xlabel(display_name, fontsize=title_fontsize, 
                         fontweight=title_fontweight, labelpad=title_pad, color=text_color)
        
        # Set grid
        if subplot_params.get('grid_enabled', True):
            grid_alpha = subplot_params.get('grid_alpha', 0.3)
            grid_axis = subplot_params.get('grid_axis', 'y')
            grid_linestyle = subplot_params.get('grid_linestyle', '-')
            grid_linewidth = subplot_params.get('grid_linewidth', 0.5)
            
            ax.grid(True, alpha=grid_alpha, axis=grid_axis, 
                   linestyle=grid_linestyle, linewidth=grid_linewidth)
        
        # Set margins with improved spacing for consistency
        subplot_margins = subplot_params.get('subplot_margins', {})
        x_margin = subplot_margins.get('x_margin', 0.05)
        y_margin = subplot_margins.get('y_margin', 0.1)
        ax.margins(x=x_margin, y=y_margin)
    
    def _get_display_name(self, variable: str) -> str:
        """
        Get the display name for visualization titles.
        Maps variable names to more concise display names for charts.
        
        Args:
            variable: Original variable name
            
        Returns:
            Display name for visualization
        """
        # Variable name mapping for visualization display
        display_mapping = {
            "Type of construct(tandem/single target)": "Type of construct"
        }
        
        return display_mapping.get(variable, variable)
    
    def _create_histogram(self, ax, data: pd.Series, variable: str, subplot_params: Dict) -> None:
        """Create histogram for numeric variables with configurable parameters."""
        histogram_params = subplot_params.get('histogram', {})
        
        # Calculate bins based on configuration
        bins_method = histogram_params.get('bins_method', 'sqrt')
        min_bins = histogram_params.get('min_bins', 5)
        max_bins = histogram_params.get('max_bins', 20)
        
        if bins_method == 'sqrt':
            bins = int(np.sqrt(len(data)))
        elif bins_method == 'sturges':
            bins = int(np.log2(len(data)) + 1)
        elif bins_method == 'fd':
            bins = 'fd'  # Freedman-Diaconis rule
        else:
            bins = 'auto'
        
        if isinstance(bins, int):
            bins = max(min_bins, min(bins, max_bins))
        
        # Get colors and styling
        primary_color = subplot_params.get('primary_color', '#2E86AB')
        edge_color = subplot_params.get('edge_color', 'black')
        edge_width = subplot_params.get('edge_width', 0.5)
        alpha = histogram_params.get('alpha', 0.7)
        
        # Create histogram
        n, bins_used, patches = ax.hist(data, bins=bins, alpha=alpha, 
                                       color=primary_color, edgecolor=edge_color, 
                                       linewidth=edge_width)
        
        # Add statistics text if enabled
        if histogram_params.get('show_stats', True):
            stats_fontsize = histogram_params.get('stats_fontsize', 8)
            stats_position = histogram_params.get('stats_position', 'top_left')
            text_color = subplot_params.get('text_color', 'black')
            
            stats_text = f'n={len(data)}\nMean: {data.mean():.1f}\nMedian: {data.median():.1f}'
            
            # Position stats text
            if stats_position == 'top_left':
                x_pos, y_pos, va = 0.02, 0.98, 'top'
            elif stats_position == 'top_right':
                x_pos, y_pos, va = 0.98, 0.98, 'top'
            else:  # bottom_left
                x_pos, y_pos, va = 0.02, 0.02, 'bottom'
            
            ax.text(x_pos, y_pos, stats_text, transform=ax.transAxes, 
                   verticalalignment=va, fontsize=stats_fontsize, color=text_color,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        # Set labels
        xlabel_fontsize = subplot_params.get('xlabel_fontsize', 10)
        ylabel_fontsize = subplot_params.get('ylabel_fontsize', 10)
        xlabel_fontweight = subplot_params.get('xlabel_fontweight', 'bold')
        ylabel_fontweight = subplot_params.get('ylabel_fontweight', 'bold')
        text_color = subplot_params.get('text_color', 'black')
        
        ax.set_xlabel(variable, fontsize=xlabel_fontsize, fontweight=xlabel_fontweight, color=text_color)
        ax.set_ylabel('Frequency', fontsize=ylabel_fontsize, fontweight=ylabel_fontweight, color=text_color)
    
    def _create_bar_chart(self, ax, data: pd.Series, variable: str, subplot_params: Dict) -> None:
        """Create bar chart for categorical variables with enhanced legend configuration."""
        bar_chart_params = subplot_params.get('bar_chart', {})
        
        # Get value counts
        value_counts = data.value_counts()
        
        # Limit to top categories if too many
        max_categories = self.config.get('visualization', 'max_categories', 10)
        if len(value_counts) > max_categories:
            value_counts = value_counts.head(max_categories)
        
        # Get colors and styling
        colors = self.config.get('visualization', 'colors', ['#2E86AB'])
        primary_color = subplot_params.get('primary_color', colors[0])
        edge_color = subplot_params.get('edge_color', 'black')
        edge_width = subplot_params.get('edge_width', 0.5)
        alpha = bar_chart_params.get('alpha', 0.8)
        
        # Assign colors to bars
        if len(value_counts) <= len(colors):
            bar_colors = colors[:len(value_counts)]
        else:
            bar_colors = [primary_color] * len(value_counts)
        
        # Calculate bar height limit based on new specifications
        # 通过y轴限制来控制条形图视觉高度，而不是缩放数据值
        max_count = value_counts.max()
        
        # Create bar chart with original values (no scaling needed)
        bars = ax.bar(range(len(value_counts)), value_counts.values, 
                     color=bar_colors, alpha=alpha, edgecolor=edge_color, linewidth=edge_width)
        
        # 控制条形图视觉高度：设置y轴上限为最大值的1.3倍（而不是默认的自动缩放）
        # 这将压缩条形图的视觉高度，同时保持子图尺寸不变
        height_compression_factor = bar_chart_params.get('height_compression_factor', 1.3)
        if max_count > 0:
            y_limit = max_count * height_compression_factor
            ax.set_ylim(0, y_limit)
        
        # Add value labels on bars if enabled
        if bar_chart_params.get('show_values', True):
            value_fontsize = bar_chart_params.get('value_fontsize', 8)
            value_fontweight = bar_chart_params.get('value_fontweight', 'bold')
            text_color = subplot_params.get('text_color', 'black')
            
            for i, (bar, count) in enumerate(zip(bars, value_counts.values)):
                height = bar.get_height()
                percentage = (count / len(data)) * 100
                # 调整标签位置：由于我们压缩了y轴，标签位置需要相应调整
                label_offset = height * 0.02  # 减少偏移量以适应压缩的y轴
                ax.text(bar.get_x() + bar.get_width()/2., height + label_offset,
                       f'{count}\n({percentage:.1f}%)', 
                       ha='center', va='bottom', fontsize=value_fontsize, 
                       fontweight=value_fontweight, color=text_color)
        
        # Set Y-axis label only (no X-axis label by default)
        ylabel_fontsize = subplot_params.get('ylabel_fontsize', 12)
        ylabel_fontweight = subplot_params.get('ylabel_fontweight', 'bold')
        text_color = subplot_params.get('text_color', 'black')
        ax.set_ylabel('Count', fontsize=ylabel_fontsize, fontweight=ylabel_fontweight, color=text_color)
        
        # Configure variable legend (right upper corner) - Default enabled
        variable_legend_config = bar_chart_params.get('variable_legend', {})
        if variable_legend_config.get('enabled', True):
            self._add_variable_legend(ax, value_counts, bar_colors, alpha, variable_legend_config)
        
        # Configure statistics legend (left upper corner)
        stats_legend_config = bar_chart_params.get('stats_legend', {})
        if stats_legend_config.get('enabled', True):
            self._add_stats_legend(ax, data, variable, stats_legend_config)
        
        # Remove X-axis tick labels (replaced by legend)
        ax.set_xticks(range(len(value_counts)))
        ax.set_xticklabels([])  # Empty labels - legend replaces these
    
    def _add_variable_legend(self, ax, value_counts, bar_colors, alpha, legend_config):
        """Add variable legend in the right upper corner with improved positioning."""
        max_label_length = legend_config.get('max_label_length', 10)  # 减少标签长度
        fontsize = legend_config.get('fontsize', 7)  # 略微减小字体
        framealpha = legend_config.get('framealpha', 0.9)
        location = legend_config.get('location', 'upper right')
        
        # Create simplified legend labels
        legend_labels = []
        for label in value_counts.index:
            label_str = str(label)
            if len(label_str) > max_label_length:
                legend_labels.append(label_str[:max_label_length] + '...')
            else:
                legend_labels.append(label_str)
        
        # Create legend handles
        legend_handles = [plt.Rectangle((0,0),1,1, color=color, alpha=alpha) 
                        for color in bar_colors]
        
        # Add legend with improved positioning to prevent overlap
        legend = ax.legend(legend_handles, legend_labels, loc=location, 
                          fontsize=fontsize, framealpha=framealpha,
                          bbox_to_anchor=(0.98, 0.98), borderaxespad=0.3,  # 调整位置防止重叠
                          handlelength=1.0, handletextpad=0.5)  # 紧凑布局
        
        # Constrain legend width to prevent overlap
        width_ratio = legend_config.get('width_ratio', 0.28)  # 减少宽度
        legend.get_frame().set_width(width_ratio)
    
    def _add_stats_legend(self, ax, data, variable, stats_config):
        """Add statistics legend in the left upper corner."""
        fontsize = stats_config.get('fontsize', 8)
        framealpha = stats_config.get('framealpha', 0.9)
        location = stats_config.get('location', 'upper left')
        show_count = stats_config.get('show_count', True)
        show_mean = stats_config.get('show_mean', True)
        
        stats_text = []
        
        # Add patient count
        if show_count:
            stats_text.append(f'n={len(data)}')
        
        # Add mean value for numeric data
        if show_mean and pd.api.types.is_numeric_dtype(data):
            mean_val = data.mean()
            stats_text.append(f'Mean: {mean_val:.1f}')
        
        # Create text box for statistics
        if stats_text:
            stats_str = '\n'.join(stats_text)
            bbox_props = dict(boxstyle='round,pad=0.3', facecolor='white', 
                            alpha=framealpha, edgecolor='gray', linewidth=0.5)
            
            ax.text(0.02, 0.98, stats_str, transform=ax.transAxes, 
                   verticalalignment='top', horizontalalignment='left',
                   fontsize=fontsize, bbox=bbox_props)
    
    def _save_figure(self, fig, filename: str) -> None:
        """
        Save figure to output directory.
        
        Args:
            fig: Matplotlib figure
            filename: Base filename (without extension)
        """
        output_dir = self.config.get_path('output_dir')
        
        # Save in multiple formats
        formats = self.config.get('visualization', 'output_formats')
        dpi = self.config.get('visualization', 'dpi')
        
        for fmt in formats:
            filepath = os.path.join(output_dir, f"{filename}.{fmt}")
            try:
                fig.savefig(filepath, dpi=dpi, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                print(f"Saved: {filepath}")
            except Exception as e:
                print(f"Error saving {filepath}: {e}")
    
    def create_summary_dashboard(self) -> None:
        """
        Create a summary dashboard with key metrics.
        创建包含关键指标的总结仪表板。
        """
        if self.df is None:
            print("Error: No data loaded. Call load_data() first.")
            return
        
        print("Creating summary dashboard...")
        
        # Create figure
        fig = plt.figure(figsize=(16, 12))
        fig.suptitle('Clinical Data Summary Dashboard', fontsize=20, fontweight='bold', y=0.98)
        
        # 1. Demographics summary (top left)
        ax1 = plt.subplot(2, 3, 1)
        self._create_demographics_summary(ax1)
        
        # 2. Disease distribution (top middle)
        ax2 = plt.subplot(2, 3, 2)
        self._create_disease_summary(ax2)
        
        # 3. Treatment history (top right)
        ax3 = plt.subplot(2, 3, 3)
        self._create_treatment_summary(ax3)
        
        # 4. Adverse events (bottom left)
        ax4 = plt.subplot(2, 3, 4)
        self._create_adverse_events_summary(ax4)
        
        # 5. Data quality (bottom middle)
        ax5 = plt.subplot(2, 3, 5)
        self._create_data_quality_summary(ax5)
        
        # 6. Key statistics (bottom right)
        ax6 = plt.subplot(2, 3, 6)
        self._create_key_statistics(ax6)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95], pad=3.0)
        
        # Save dashboard
        self._save_figure(fig, "summary_dashboard")
        plt.close(fig)
        
        print("Summary dashboard created!")
    
    def _create_demographics_summary(self, ax) -> None:
        """Create demographics summary plot."""
        # Sex distribution
        if 'Sex' in self.df.columns:
            sex_counts = self.df['Sex'].value_counts()
            colors = ['lightblue', 'lightpink']
            wedges, texts, autotexts = ax.pie(sex_counts.values, labels=sex_counts.index, 
                                             colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title('Sex Distribution', fontweight='bold', pad=20)
        else:
            ax.text(0.5, 0.5, 'No sex data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Sex Distribution', fontweight='bold', pad=20)
    
    def _create_disease_summary(self, ax) -> None:
        """Create disease summary plot."""
        if 'Disease' in self.df.columns:
            disease_counts = self.df['Disease'].value_counts().head(5)
            bars = ax.bar(range(len(disease_counts)), disease_counts.values, 
                         color='lightcoral', alpha=0.8)
            ax.set_title('Top 5 Diseases', fontweight='bold', pad=20)
            ax.set_xticks(range(len(disease_counts)))
            ax.set_xticklabels([str(d)[:10] + '...' if len(str(d)) > 10 else str(d) 
                               for d in disease_counts.index], rotation=45, ha='right')
            ax.set_ylabel('Count')
            
            # Add value labels
            for bar, count in zip(bars, disease_counts.values):
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                       str(count), ha='center', va='bottom', fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No disease data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Disease Distribution', fontweight='bold', pad=20)
    
    def _create_treatment_summary(self, ax) -> None:
        """Create treatment summary plot."""
        if 'Number of prior therapy lines' in self.df.columns:
            therapy_lines = self.df['Number of prior therapy lines'].dropna()
            ax.hist(therapy_lines, bins=range(int(therapy_lines.min()), int(therapy_lines.max()) + 2), 
                   alpha=0.7, color='lightgreen', edgecolor='black')
            ax.set_title('Prior Therapy Lines', fontweight='bold', pad=20)
            ax.set_xlabel('Number of Lines')
            ax.set_ylabel('Count')
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'No therapy data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Treatment History', fontweight='bold', pad=20)
    
    def _create_adverse_events_summary(self, ax) -> None:
        """Create adverse events summary plot."""
        ae_vars = ['CRS grade', 'ICANS grade']
        ae_data = []
        labels = []
        
        for var in ae_vars:
            if var in self.df.columns:
                # Count patients with any grade > 0
                any_grade = (self.df[var].dropna() > 0).sum()
                total_with_data = self.df[var].dropna().shape[0]
                if total_with_data > 0:
                    percentage = (any_grade / total_with_data) * 100
                    ae_data.append(percentage)
                    labels.append(var.replace(' grade', ''))
        
        if ae_data:
            bars = ax.bar(labels, ae_data, color=['orange', 'red'], alpha=0.8)
            ax.set_title('Adverse Events Rate (Any Grade)', fontweight='bold', pad=20)
            ax.set_ylabel('Percentage (%)')
            ax.set_ylim(0, 100)
            
            # Add value labels
            for bar, value in zip(bars, ae_data):
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                       f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No adverse events data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Adverse Events', fontweight='bold', pad=20)
    
    def _create_data_quality_summary(self, ax) -> None:
        """Create data quality summary plot."""
        # Calculate missing data percentages
        missing_percentages = (self.df.isnull().sum() / len(self.df) * 100).sort_values(ascending=True)
        
        # Show top 10 variables with most missing data
        top_missing = missing_percentages.tail(10)
        
        if len(top_missing) > 0 and top_missing.max() > 0:
            bars = ax.barh(range(len(top_missing)), top_missing.values, color='gray', alpha=0.7)
            ax.set_title('Missing Data by Variable', fontweight='bold', pad=20)
            ax.set_yticks(range(len(top_missing)))
            ax.set_yticklabels([str(var)[:15] + '...' if len(str(var)) > 15 else str(var) 
                               for var in top_missing.index])
            ax.set_xlabel('Missing Percentage (%)')
            
            # Add value labels
            for bar, value in zip(bars, top_missing.values):
                ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2.,
                       f'{value:.1f}%', ha='left', va='center', fontsize=8)
        else:
            ax.text(0.5, 0.5, 'No missing data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Data Quality', fontweight='bold', pad=20)
    
    def _create_key_statistics(self, ax) -> None:
        """Create key statistics summary."""
        # Prepare key statistics
        stats_text = []
        stats_text.append(f"Total Patients: {self.total_patients}")
        stats_text.append(f"Total Variables: {self.df.shape[1]}")
        
        # Age statistics
        if 'Age' in self.df.columns:
            age_data = self.df['Age'].dropna()
            if len(age_data) > 0:
                stats_text.append(f"Mean Age: {age_data.mean():.1f}")
                stats_text.append(f"Age Range: {age_data.min():.0f}-{age_data.max():.0f}")
        
        # Data completeness
        total_cells = self.df.shape[0] * self.df.shape[1]
        missing_cells = self.df.isnull().sum().sum()
        completeness = ((total_cells - missing_cells) / total_cells) * 100
        stats_text.append(f"Data Completeness: {completeness:.1f}%")
        
        # Disease diversity
        if 'Disease' in self.df.columns:
            unique_diseases = self.df['Disease'].nunique()
            stats_text.append(f"Unique Diseases: {unique_diseases}")
        
        # Display statistics
        ax.text(0.05, 0.95, '\n'.join(stats_text), transform=ax.transAxes, 
               fontsize=12, verticalalignment='top', fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
        
        ax.set_title('Key Statistics', fontweight='bold', pad=20)
        ax.axis('off')
