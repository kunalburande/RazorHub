import React, { useState, useEffect, useRef } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from '../i18n/LocaleContext';
import {
  AlertTriangle,
  Bell,
  Check,
  CreditCard,
  Database,
  Download,
  KeyRound,
  LayoutDashboard,
  Loader2,
  Lock,
  Mail,
  Moon,
  Palette,
  Save,
  ShieldCheck,
  ShoppingBag,
  Sliders,
  Smartphone,
  Sparkles,
  Sun,
  Trash2,
  Upload,
  User,
  X,
} from 'lucide-react';
import type { Role } from '../context/AuthContext';

const PRESET_AVATARS = [
  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=300&q=80',
];

export default function DashboardHome() {
  const { user } = useAuth();

  if (user?.effective_role === 'seller') return <Navigate to="/seller" replace />;
  if (user?.effective_role === 'admin') return <Navigate to="/admin" replace />;
  return <CustomerDashboard />;
}

function CustomerDashboard() {
  const { user, isDemo, requestDeleteAccount, confirmDeleteAccount } = useAuth();
  const { theme, setTheme } = useTheme();
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [activeTab, setActiveTab] = useState<
    'profile' | 'appearance' | 'preferences' | 'notifications' | 'security' | 'data'
  >('profile');

  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info'; title: string; message: string } | null>(null);

  function showToast(type: 'success' | 'error' | 'info', title: string, message: string) {
    setToast({ type, title, message });
    setTimeout(() => setToast(null), 4000);
  }

  // Profile State
  const [avatarUrl, setAvatarUrl] = useState<string>(() => {
    return localStorage.getItem('razorhub_user_avatar') || PRESET_AVATARS[0];
  });
  const getUserDisplayName = () => {
    if (!user) return 'Rahul Sharma';
    const combined = [user.first_name, user.last_name].filter(Boolean).join(' ').trim();
    return combined || user.username || 'Rahul Sharma';
  };

  const [profile, setProfile] = useState({
    fullName: getUserDisplayName(),
    email: user?.email || 'rahul.sharma@example.com',
    roleDescription: 'Verified Customer',
    phone: user?.phone || '+91 98765 43210',
    city: 'Bengaluru',
    pincode: '560001',
    bio: 'Customer at RazorHub. Prefer fast delivery and evening drop-offs.',
  });

  useEffect(() => {
    if (user) {
      setProfile((prev) => ({
        ...prev,
        fullName: [user.first_name, user.last_name].filter(Boolean).join(' ').trim() || user.username || prev.fullName,
        email: user.email || prev.email,
        phone: user.phone || prev.phone,
      }));
    }
  }, [user]);

  // Appearance & Theme State
  const [accentColor, setAccentColor] = useState<'blue' | 'indigo' | 'emerald' | 'amber' | 'rose'>('blue');
  const [density, setDensity] = useState<'comfortable' | 'compact'>('comfortable');

  // Preferences State
  const [preferences, setPreferences] = useState({
    currency: 'INR (₹)',
    language: 'English',
    defaultPayment: 'UPI (GPay / PhonePe / Paytm)',
    oneClickCheckout: true,
    saveAddresses: true,
  });

  // Notifications State
  const [notifications, setNotifications] = useState({
    orderUpdates: true,
    whatsappAlerts: true,
    priceDropAlerts: true,
    promotions: false,
    newsletter: false,
  });

  // Security State
  const [passwords, setPasswords] = useState({
    current: '',
    newPass: '',
    confirmPass: '',
  });
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);

  // Delete Modal State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteStep, setDeleteStep] = useState<'confirm' | 'otp'>('confirm');
  const [otpCode, setOtpCode] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Avatar Upload Handler
  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      showToast('error', 'File Too Large', 'Please select an image under 5MB.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target?.result as string;
      setAvatarUrl(dataUrl);
      localStorage.setItem('razorhub_user_avatar', dataUrl);
      showToast('success', 'Avatar Updated', 'Your profile picture has been updated.');
    };
    reader.readAsDataURL(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const selectPresetAvatar = (url: string) => {
    setAvatarUrl(url);
    localStorage.setItem('razorhub_user_avatar', url);
    showToast('success', 'Avatar Selected', 'Profile avatar changed successfully.');
  };

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('razorhub_customer_profile', JSON.stringify(profile));
    showToast('success', 'Changes Saved', 'Your profile details have been saved successfully.');
  };

  const handleSavePreferences = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('razorhub_customer_preferences', JSON.stringify(preferences));
    showToast('success', 'Preferences Saved', 'Shopping and checkout preferences updated.');
  };

  const handleSaveNotifications = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('razorhub_customer_notifications', JSON.stringify(notifications));
    showToast('success', 'Notifications Updated', 'Your notification preferences have been saved.');
  };

  const handlePasswordChange = (e: React.FormEvent) => {
    e.preventDefault();
    if (!passwords.newPass || passwords.newPass !== passwords.confirmPass) {
      showToast('error', 'Password Mismatch', 'New password and confirm password must match.');
      return;
    }
    setPasswords({ current: '', newPass: '', confirmPass: '' });
    showToast('success', 'Password Updated', 'Your account password has been changed.');
  };

  const handleExportData = (format: 'json' | 'csv') => {
    const exportData = {
      user: { email: user?.email, name: profile.fullName, phone: profile.phone },
      profile,
      preferences,
      notifications,
      exportedAt: new Date().toISOString(),
    };

    let blob: Blob;
    let filename: string;

    if (format === 'json') {
      blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      filename = `razorhub-account-${Date.now()}.json`;
    } else {
      const csvRows = [
        ['Field', 'Value'],
        ['Full Name', profile.fullName],
        ['Email', profile.email],
        ['Phone', profile.phone],
        ['City', profile.city],
        ['Pincode', profile.pincode],
        ['Currency', preferences.currency],
      ];
      const csvContent = csvRows.map((e) => e.join(',')).join('\n');
      blob = new Blob([csvContent], { type: 'text/csv' });
      filename = `razorhub-account-${Date.now()}.csv`;
    }

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast('success', 'Export Complete', `Downloaded account details as ${format.toUpperCase()}.`);
  };

  async function handleRequestOTP() {
    setDeleteError('');
    setDeleteLoading(true);
    try {
      await requestDeleteAccount();
      setDeleteStep('otp');
    } catch (err: any) {
      setDeleteError(err.message || 'Failed to send verification code.');
    } finally {
      setDeleteLoading(false);
    }
  }

  async function handleConfirmDelete() {
    if (!otpCode.trim()) {
      setDeleteError('Please enter the verification code.');
      return;
    }
    setDeleteError('');
    setDeleteLoading(true);
    try {
      await confirmDeleteAccount(otpCode.trim());
    } catch (err: any) {
      setDeleteError(err.message || 'Invalid or expired verification code.');
      setDeleteLoading(false);
    }
  }

  function closeDeleteModal() {
    setShowDeleteModal(false);
    setDeleteStep('confirm');
    setOtpCode('');
    setDeleteError('');
    setDeleteLoading(false);
  }

  const tabs = [
    { id: 'profile' as const, label: 'Profile Settings', icon: User },
    { id: 'appearance' as const, label: 'Appearance', icon: Palette },
    { id: 'preferences' as const, label: 'Preferences', icon: LayoutDashboard },
    { id: 'notifications' as const, label: 'Notifications', icon: Bell },
    { id: 'security' as const, label: 'Security & Auth', icon: ShieldCheck },
    { id: 'data' as const, label: 'Data & Export', icon: Database },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Toast feedback */}
      {toast && (
        <div
          className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-xl border px-4 py-3 shadow-xl backdrop-blur-md transition-all anim-fade-in-up ${
            toast.type === 'error'
              ? 'border-red-200 bg-red-500/90 text-white'
              : 'border-blue-200 bg-blue-600/95 text-white'
          }`}
        >
          <Sparkles className="h-5 w-5 shrink-0" />
          <div>
            <p className="text-sm font-bold leading-none">{toast.title}</p>
            <p className="text-xs opacity-90 mt-0.5">{toast.message}</p>
          </div>
        </div>
      )}

      {/* ── Top Header (Image 1 Style) ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-border/60">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-primary flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-blue-500/10 text-accent">
              <Sliders className="h-6 w-6" />
            </span>
            Dashboard Settings
          </h1>
          <p className="mt-1 text-sm text-secondary">
            Manage your account credentials, dark aesthetics, notifications, and data exports.
          </p>
        </div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold bg-blue-500/10 text-accent border border-blue-500/20 self-start sm:self-center shadow-xs">
          <Sparkles className="h-3.5 w-3.5" />
          Customer Hub v2.4
        </div>
      </div>

      {isDemo && (
        <div className="rounded-xl border border-accent/30 bg-accent/5 p-4 text-xs font-semibold text-accent flex items-center gap-2.5">
          <Sparkles className="h-4 w-4 shrink-0" />
          <span>Demo mode active: You can explore and test all settings. Changes will reset on page reload.</span>
        </div>
      )}

      {/* ── Main Tabbed Layout (Image 1 Style) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* ── Left Navigation Sidebar ── */}
        <div className="lg:col-span-1 rounded-2xl border border-border bg-surface p-2.5 shadow-sm space-y-1.5">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-bold transition-all text-left ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-sky-600 text-white shadow-md shadow-blue-500/20'
                    : 'text-secondary hover:bg-muted/60 hover:text-primary'
                }`}
              >
                <Icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-white' : 'text-secondary'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* ── Right Content Panel ── */}
        <div className="lg:col-span-3 rounded-2xl border border-border bg-surface p-6 sm:p-8 shadow-sm">
          {/* TAB 1: Profile Settings */}
          {activeTab === 'profile' && (
            <div>
              <div className="mb-6">
                <h2 className="text-xl font-black text-primary">Profile Information</h2>
                <p className="text-sm text-secondary mt-1">
                  Update your public profile details and personal shopper persona.
                </p>
              </div>

              {/* Profile Photo & Avatar Section (Image 1 Style) */}
              <div className="rounded-xl border border-border/80 bg-background/50 p-5 mb-6">
                <h3 className="text-xs font-bold uppercase tracking-wider text-secondary mb-4">
                  Profile Photo &amp; Avatar
                </h3>
                <div className="flex flex-col sm:flex-row items-center gap-6">
                  <div className="relative group shrink-0">
                    <img
                      src={avatarUrl}
                      alt="User Avatar"
                      className="h-20 w-20 rounded-full object-cover border-2 border-accent shadow-md"
                    />
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="absolute bottom-0 right-0 h-7 w-7 rounded-full bg-accent text-white flex items-center justify-center shadow-md hover:scale-110 transition-transform"
                      title="Upload custom photo"
                    >
                      <Upload className="h-3.5 w-3.5" />
                    </button>
                  </div>

                  <div className="flex-1 text-center sm:text-left space-y-3">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleAvatarUpload}
                    />
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="px-4 py-2 rounded-xl border border-border bg-surface hover:bg-muted font-bold text-xs text-primary transition-colors shadow-xs"
                    >
                      Upload Custom Photo
                    </button>
                    <p className="text-xs text-secondary">
                      Upload any JPG, PNG or WebP image file from your device.
                    </p>

                    <div>
                      <span className="block text-[10px] font-bold uppercase tracking-wider text-secondary mb-2">
                        OR PICK A PRESET AVATAR:
                      </span>
                      <div className="flex items-center gap-2 justify-center sm:justify-start flex-wrap">
                        {PRESET_AVATARS.map((preset, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => selectPresetAvatar(preset)}
                            className={`relative h-9 w-9 rounded-full overflow-hidden border-2 transition-all hover:scale-110 ${
                              avatarUrl === preset ? 'border-accent ring-2 ring-accent/30 scale-105' : 'border-transparent opacity-80 hover:opacity-100'
                            }`}
                          >
                            <img src={preset} alt={`Preset ${idx + 1}`} className="h-full w-full object-cover" />
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Profile Form */}
              <form onSubmit={handleSaveProfile} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1.5">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={profile.fullName}
                      onChange={(e) => setProfile({ ...profile, fullName: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-primary font-medium focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                      placeholder="Your full name"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1.5">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={profile.email}
                      onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-primary font-medium focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                      placeholder="you@example.com"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1.5">
                      Phone Number
                    </label>
                    <input
                      type="tel"
                      value={profile.phone}
                      onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-primary font-medium focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                      placeholder="+91 98765 43210"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1.5">
                      Role Description
                    </label>
                    <input
                      type="text"
                      value={profile.roleDescription}
                      disabled
                      className="w-full rounded-xl border border-border bg-muted/40 px-4 py-3 text-sm text-secondary font-medium cursor-not-allowed"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1.5">
                      Delivery City
                    </label>
                    <input
                      type="text"
                      value={profile.city}
                      onChange={(e) => setProfile({ ...profile, city: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-primary font-medium focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                      placeholder="Bengaluru"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1.5">
                      Delivery Pincode
                    </label>
                    <input
                      type="text"
                      value={profile.pincode}
                      onChange={(e) => setProfile({ ...profile, pincode: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-primary font-medium focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                      placeholder="560001"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1.5">
                    Bio / Delivery Notes
                  </label>
                  <textarea
                    rows={3}
                    value={profile.bio}
                    onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                    className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-primary font-medium focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent transition-all"
                    placeholder="Provide any delivery landmarks or special instructions..."
                  />
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-sky-600 px-6 py-3.5 text-sm font-bold text-white shadow-md shadow-blue-500/20 hover:opacity-95 transition-opacity"
                  >
                    <Save className="h-4 w-4" />
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* TAB 2: Appearance */}
          {activeTab === 'appearance' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-black text-primary">Appearance &amp; Theme</h2>
                <p className="text-sm text-secondary mt-1">
                  Customize the visual styling, theme mode, and interface density of your portal.
                </p>
              </div>

              {/* Theme Selector */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-3">
                  Theme Mode
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <button
                    type="button"
                    onClick={() => setTheme('light')}
                    className={`flex items-center gap-3 p-4 rounded-xl border-2 text-left transition-all ${
                      theme === 'light'
                        ? 'border-accent bg-blue-50/40 dark:bg-blue-950/20'
                        : 'border-border bg-background hover:border-border/80'
                    }`}
                  >
                    <div className="h-10 w-10 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center shrink-0">
                      <Sun className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-bold text-sm text-primary">Light Aesthetics</p>
                      <p className="text-xs text-secondary">Clean, crisp high-contrast day theme</p>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => setTheme('dark')}
                    className={`flex items-center gap-3 p-4 rounded-xl border-2 text-left transition-all ${
                      theme === 'dark'
                        ? 'border-accent bg-blue-50/40 dark:bg-blue-950/20'
                        : 'border-border bg-background hover:border-border/80'
                    }`}
                  >
                    <div className="h-10 w-10 rounded-xl bg-indigo-900/60 text-indigo-300 flex items-center justify-center shrink-0">
                      <Moon className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-bold text-sm text-primary">Dark Aesthetics</p>
                      <p className="text-xs text-secondary">Deep slate dark mode for night shopping</p>
                    </div>
                  </button>
                </div>
              </div>

              {/* Accent Color Selection */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-3">
                  Accent Color Palette
                </label>
                <div className="flex items-center gap-3 flex-wrap">
                  {[
                    { id: 'blue' as const, bg: 'bg-blue-600', name: 'Electric Blue' },
                    { id: 'indigo' as const, bg: 'bg-indigo-600', name: 'Indigo Glow' },
                    { id: 'emerald' as const, bg: 'bg-emerald-600', name: 'Emerald Green' },
                    { id: 'amber' as const, bg: 'bg-amber-600', name: 'Amber Gold' },
                    { id: 'rose' as const, bg: 'bg-rose-600', name: 'Rose Crimson' },
                  ].map((color) => (
                    <button
                      key={color.id}
                      type="button"
                      onClick={() => {
                        setAccentColor(color.id);
                        showToast('info', 'Accent Changed', `Applied ${color.name} palette.`);
                      }}
                      className={`flex items-center gap-2 px-3.5 py-2 rounded-xl border text-xs font-bold transition-all ${
                        accentColor === color.id
                          ? 'border-accent bg-accent/10 text-primary ring-2 ring-accent/20'
                          : 'border-border bg-background text-secondary hover:text-primary'
                      }`}
                    >
                      <span className={`h-3.5 w-3.5 rounded-full ${color.bg}`} />
                      {color.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Density Selection */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-3">
                  Display Density
                </label>
                <div className="grid grid-cols-2 gap-4 max-w-md">
                  <button
                    type="button"
                    onClick={() => setDensity('comfortable')}
                    className={`p-3.5 rounded-xl border text-xs font-bold text-center transition-all ${
                      density === 'comfortable' ? 'border-accent bg-accent/10 text-accent' : 'border-border bg-background text-secondary'
                    }`}
                  >
                    Comfortable (Standard)
                  </button>
                  <button
                    type="button"
                    onClick={() => setDensity('compact')}
                    className={`p-3.5 rounded-xl border text-xs font-bold text-center transition-all ${
                      density === 'compact' ? 'border-accent bg-accent/10 text-accent' : 'border-border bg-background text-secondary'
                    }`}
                  >
                    Compact (High Info)
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: Preferences */}
          {activeTab === 'preferences' && (
            <div>
              <div className="mb-6">
                <h2 className="text-xl font-black text-primary">Shopping Preferences</h2>
                <p className="text-sm text-secondary mt-1">
                  Configure default regional currency, preferred payment methods, and express checkout.
                </p>
              </div>

              <form onSubmit={handleSavePreferences} className="space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1.5">
                      Primary Currency
                    </label>
                    <select
                      value={preferences.currency}
                      onChange={(e) => setPreferences({ ...preferences, currency: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-primary font-medium focus:border-accent focus:outline-none"
                    >
                      <option value="INR (₹)">INR (₹) — Indian Rupee</option>
                      <option value="USD ($)">USD ($) — US Dollar</option>
                      <option value="NPR (रू)">NPR (रू) — Nepalese Rupee</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1.5">
                      Preferred Language
                    </label>
                    <select
                      value={preferences.language}
                      onChange={(e) => setPreferences({ ...preferences, language: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-primary font-medium focus:border-accent focus:outline-none"
                    >
                      <option value="English">English</option>
                      <option value="Hindi">हिंदी (Hindi)</option>
                      <option value="Nepali">नेपाली (Nepali)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1.5">
                    Default Payment Method
                  </label>
                  <select
                    value={preferences.defaultPayment}
                    onChange={(e) => setPreferences({ ...preferences, defaultPayment: e.target.value })}
                    className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-primary font-medium focus:border-accent focus:outline-none"
                  >
                    <option value="UPI (GPay / PhonePe / Paytm)">UPI (GPay / PhonePe / Paytm / QR)</option>
                    <option value="Credit / Debit Card">Credit / Debit Card (Visa / Mastercard / RuPay)</option>
                    <option value="Cash on Delivery">Cash on Delivery (Pay at Doorstep)</option>
                  </select>
                </div>

                <div className="space-y-3 pt-2">
                  <label className="flex items-center gap-3 p-3.5 rounded-xl border border-border bg-background cursor-pointer hover:bg-muted/40 transition-colors">
                    <input
                      type="checkbox"
                      checked={preferences.oneClickCheckout}
                      onChange={(e) => setPreferences({ ...preferences, oneClickCheckout: e.target.checked })}
                      className="h-4 w-4 rounded border-border text-accent focus:ring-accent"
                    />
                    <div>
                      <p className="text-sm font-bold text-primary">Enable Express 1-Click Checkout</p>
                      <p className="text-xs text-secondary">Auto-select default address and UPI payment during checkout.</p>
                    </div>
                  </label>

                  <label className="flex items-center gap-3 p-3.5 rounded-xl border border-border bg-background cursor-pointer hover:bg-muted/40 transition-colors">
                    <input
                      type="checkbox"
                      checked={preferences.saveAddresses}
                      onChange={(e) => setPreferences({ ...preferences, saveAddresses: e.target.checked })}
                      className="h-4 w-4 rounded border-border text-accent focus:ring-accent"
                    />
                    <div>
                      <p className="text-sm font-bold text-primary">Auto-save addresses to address book</p>
                      <p className="text-xs text-secondary">Save new shipping addresses entered during past orders.</p>
                    </div>
                  </label>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-sky-600 px-6 py-3.5 text-sm font-bold text-white shadow-md shadow-blue-500/20 hover:opacity-95 transition-opacity"
                  >
                    <Save className="h-4 w-4" />
                    Save Preferences
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* TAB 4: Notifications */}
          {activeTab === 'notifications' && (
            <div>
              <div className="mb-6">
                <h2 className="text-xl font-black text-primary">Notification Settings</h2>
                <p className="text-sm text-secondary mt-1">
                  Manage communication channels, order alerts, and promotional newsletters.
                </p>
              </div>

              <form onSubmit={handleSaveNotifications} className="space-y-4">
                {[
                  {
                    key: 'orderUpdates' as const,
                    title: 'Email Order Confirmations & Invoices',
                    desc: 'Receive immediate email receipts, invoices, and delivery timeline tracking.',
                  },
                  {
                    key: 'whatsappAlerts' as const,
                    title: 'WhatsApp & SMS Dispatch Updates',
                    desc: 'Get real-time tracking links on WhatsApp when items are shipped from sellers.',
                  },
                  {
                    key: 'priceDropAlerts' as const,
                    title: 'Wishlist Price Drops & Restock Alerts',
                    desc: 'Instant notifications when saved items go on sale or return to stock.',
                  },
                  {
                    key: 'promotions' as const,
                    title: 'Exclusive Flash Deals & Seasonal Offers',
                    desc: 'Occasional curated promotions from nearby neighborhood sellers.',
                  },
                ].map((item) => (
                  <label
                    key={item.key}
                    className="flex items-start gap-3.5 p-4 rounded-xl border border-border bg-background cursor-pointer hover:bg-muted/40 transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={notifications[item.key]}
                      onChange={(e) => setNotifications({ ...notifications, [item.key]: e.target.checked })}
                      className="mt-1 h-4 w-4 rounded border-border text-accent focus:ring-accent"
                    />
                    <div className="flex-1">
                      <p className="text-sm font-bold text-primary">{item.title}</p>
                      <p className="text-xs text-secondary mt-0.5">{item.desc}</p>
                    </div>
                  </label>
                ))}

                <div className="pt-3">
                  <button
                    type="submit"
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-sky-600 px-6 py-3.5 text-sm font-bold text-white shadow-md shadow-blue-500/20 hover:opacity-95 transition-opacity"
                  >
                    <Save className="h-4 w-4" />
                    Save Notification Rules
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* TAB 5: Security & Auth */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-black text-primary">Security &amp; Authentication</h2>
                <p className="text-sm text-secondary mt-1">
                  Manage your account credentials, password changes, and two-factor authentication.
                </p>
              </div>

              {/* Password Change Card */}
              <div className="rounded-xl border border-border p-5 bg-background/50">
                <h3 className="text-sm font-bold text-primary mb-4 flex items-center gap-2">
                  <KeyRound className="h-4 w-4 text-accent" />
                  Change Password
                </h3>
                <form onSubmit={handlePasswordChange} className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1.5">
                      Current Password
                    </label>
                    <input
                      type="password"
                      value={passwords.current}
                      onChange={(e) => setPasswords({ ...passwords, current: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-primary font-medium focus:border-accent focus:outline-none"
                      placeholder="••••••••"
                      required
                    />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1.5">
                        New Password
                      </label>
                      <input
                        type="password"
                        value={passwords.newPass}
                        onChange={(e) => setPasswords({ ...passwords, newPass: e.target.value })}
                        className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-primary font-medium focus:border-accent focus:outline-none"
                        placeholder="••••••••"
                        required
                        minLength={6}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1.5">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        value={passwords.confirmPass}
                        onChange={(e) => setPasswords({ ...passwords, confirmPass: e.target.value })}
                        className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm text-primary font-medium focus:border-accent focus:outline-none"
                        placeholder="••••••••"
                        required
                        minLength={6}
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-border bg-surface hover:bg-muted font-bold text-xs text-primary transition-colors"
                  >
                    Update Password
                  </button>
                </form>
              </div>

              {/* 2FA Toggle Card */}
              <div className="rounded-xl border border-border p-5 bg-background/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-bold text-primary flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-green-500" />
                    Two-Factor Authentication (2FA)
                  </h3>
                  <p className="text-xs text-secondary mt-1">
                    Require a one-time verification code (OTP) sent to your email on every login.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setTwoFactorEnabled(!twoFactorEnabled);
                    showToast('success', '2FA Setting Updated', `Two-Factor Auth is now ${!twoFactorEnabled ? 'Enabled' : 'Disabled'}.`);
                  }}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                    twoFactorEnabled ? 'bg-green-600 text-white' : 'border border-border bg-surface text-secondary hover:text-primary'
                  }`}
                >
                  {twoFactorEnabled ? '2FA Enabled' : 'Enable 2FA'}
                </button>
              </div>

              {/* Active Session info */}
              <div className="rounded-xl border border-border p-5 bg-background/50">
                <h3 className="text-xs font-bold uppercase tracking-wider text-secondary mb-3">
                  Current Session
                </h3>
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2.5">
                    <Smartphone className="h-4 w-4 text-accent" />
                    <div>
                      <p className="font-bold text-primary">Web Browser Session</p>
                      <p className="text-secondary">{user?.email}</p>
                    </div>
                  </div>
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-500/10 text-green-600 font-bold text-[10px]">
                    <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
                    Active Now
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: Data & Export */}
          {activeTab === 'data' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-black text-primary">Data &amp; Account Privacy</h2>
                <p className="text-sm text-secondary mt-1">
                  Download copies of your order records, export saved details, or request permanent deletion.
                </p>
              </div>

              {/* Export Data Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="rounded-xl border border-border bg-background/50 p-5 space-y-3">
                  <div className="h-9 w-9 rounded-xl bg-blue-500/10 text-accent flex items-center justify-center">
                    <Download className="h-4 w-4" />
                  </div>
                  <h3 className="font-bold text-sm text-primary">Export Account Data (JSON)</h3>
                  <p className="text-xs text-secondary leading-relaxed">
                    Download complete structured JSON file with your profile, preferences, and activity settings.
                  </p>
                  <button
                    type="button"
                    onClick={() => handleExportData('json')}
                    className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-border bg-surface hover:bg-muted font-bold text-xs text-primary transition-colors"
                  >
                    <Download className="h-3.5 w-3.5" />
                    Download JSON
                  </button>
                </div>

                <div className="rounded-xl border border-border bg-background/50 p-5 space-y-3">
                  <div className="h-9 w-9 rounded-xl bg-indigo-500/10 text-indigo-500 flex items-center justify-center">
                    <Database className="h-4 w-4" />
                  </div>
                  <h3 className="font-bold text-sm text-primary">Export Summary (CSV)</h3>
                  <p className="text-xs text-secondary leading-relaxed">
                    Download spreadsheet-ready CSV summary containing your profile details and preferences.
                  </p>
                  <button
                    type="button"
                    onClick={() => handleExportData('csv')}
                    className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-border bg-surface hover:bg-muted font-bold text-xs text-primary transition-colors"
                  >
                    <Download className="h-3.5 w-3.5" />
                    Download CSV
                  </button>
                </div>
              </div>

              {/* Danger Zone */}
              {!isDemo && (
                <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-5 mt-6 space-y-3">
                  <div className="flex items-center gap-2 text-red-600 font-bold text-sm">
                    <AlertTriangle className="h-4 w-4" />
                    Danger Zone
                  </div>
                  <p className="text-xs text-secondary leading-relaxed">
                    Once you delete your account, all personal profile records, order histories, and saved preferences are permanently erased.
                  </p>
                  <button
                    type="button"
                    onClick={() => setShowDeleteModal(true)}
                    className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-xl transition-colors text-xs shadow-sm"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Delete Account
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Delete Account Modal (OTP Flow) */}
      {showDeleteModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 py-6 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
        >
          <div className="anim-scale-in w-full max-w-md rounded-2xl border border-border bg-surface p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-100 dark:bg-red-950 text-red-600">
                  <AlertTriangle className="h-5 w-5" />
                </span>
                <h3 className="text-lg font-bold text-primary">Delete Account</h3>
              </div>
              <button
                type="button"
                onClick={closeDeleteModal}
                className="h-8 w-8 rounded-lg border border-border text-secondary hover:text-primary flex items-center justify-center"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {deleteStep === 'confirm' ? (
              <>
                <p className="text-sm text-secondary leading-relaxed mb-2">
                  You are about to permanently delete your account <strong className="text-primary">{user?.email}</strong>.
                </p>
                <p className="text-xs text-secondary leading-relaxed mb-6">
                  A 6-digit verification code will be sent to your email to confirm this action.
                </p>

                {deleteError && (
                  <p className="mb-4 rounded-xl bg-red-50 dark:bg-red-950/40 p-3 text-xs text-red-700 dark:text-red-300 border border-red-200">
                    {deleteError}
                  </p>
                )}

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={closeDeleteModal}
                    className="flex-1 rounded-xl border border-border bg-background py-2.5 text-xs font-bold text-secondary hover:text-primary"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleRequestOTP}
                    disabled={deleteLoading}
                    className="flex-1 rounded-xl bg-red-600 py-2.5 text-xs font-bold text-white hover:bg-red-700 disabled:opacity-60 flex items-center justify-center gap-2"
                  >
                    {deleteLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                    Send Code
                  </button>
                </div>
              </>
            ) : (
              <>
                <p className="text-sm text-secondary leading-relaxed mb-4">
                  A 6-digit code has been sent to <strong className="text-primary">{user?.email}</strong>. Enter it below to confirm permanent deletion.
                </p>

                {deleteError && (
                  <p className="mb-4 rounded-xl bg-red-50 dark:bg-red-950/40 p-3 text-xs text-red-700 dark:text-red-300 border border-red-200">
                    {deleteError}
                  </p>
                )}

                <input
                  type="text"
                  maxLength={6}
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                  placeholder="••••••"
                  className="mb-6 w-full rounded-xl border border-border bg-background px-4 py-3.5 text-center text-2xl font-mono tracking-[0.5em] outline-none focus:border-red-500"
                  autoFocus
                />

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => { setDeleteStep('confirm'); setOtpCode(''); setDeleteError(''); }}
                    className="flex-1 rounded-xl border border-border bg-background py-2.5 text-xs font-bold text-secondary hover:text-primary"
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    onClick={handleConfirmDelete}
                    disabled={deleteLoading || otpCode.length < 6}
                    className="flex-1 rounded-xl bg-red-600 py-2.5 text-xs font-bold text-white hover:bg-red-700 disabled:opacity-60 flex items-center justify-center gap-2"
                  >
                    {deleteLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                    Delete Permanently
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
