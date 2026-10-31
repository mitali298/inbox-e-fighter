import React, { useState } from 'react';
import { ArcadeNavbar } from './components/common/ArcadeNavbar';
import { GmailModal } from './components/common/GmailModal';
import { HeroSection } from './components/home/HeroSection';
import { PlayerProfile } from './components/home/PlayerProfile';
import { InboxHealth } from './components/home/InboxHealth';
import { HowToPlay } from './components/home/HowToPlay';
import { ArcadeFooter } from './components/home/ArcadeFooter';
import { BattleArena } from './components/game/BattleArena';
import { INITIAL_PLAYER_STATS } from './services/mockData';
import { PlayerStats, GameView } from './types/game';

export const App: React.FC = () => {
  const [playerStats, setPlayerStats] = useState<PlayerStats>(INITIAL_PLAYER_STATS);
  const [currentView, setCurrentView] = useState<GameView>('home');
  const [isGmailModalOpen, setIsGmailModalOpen] = useState(false);
  const [isCrtOn, setIsCrtOn] = useState(false);
  const [isMuted, setIsMuted] = useState(false);

  return (
    <div className={`min-h-screen cyber-bg text-slate-100 ${isCrtOn ? 'crt' : ''} selection:bg-cyber-pink selection:text-white`}>
      
      {/* Top Arcade Navigation */}
      <ArcadeNavbar
        playerStats={playerStats}
        isCrtOn={isCrtOn}
        setIsCrtOn={setIsCrtOn}
        isMuted={isMuted}
        setIsMuted={setIsMuted}
        onOpenGmailModal={() => setIsGmailModalOpen(true)}
        onStartGame={() => setCurrentView('arena')}
        currentView={currentView}
        onGoHome={() => setCurrentView('home')}
      />

      {/* Main View Router */}
      <main className="transition-all duration-300">
        {currentView === 'home' ? (
          <div>
            {/* 1. Hero Section (with Tagline, Fighter vs Monster, Attack simulation, Start Game, Play Demo, Connect Gmail) */}
            <HeroSection
              onStartGame={() => setCurrentView('arena')}
              onPlayDemo={() => setCurrentView('arena')}
              onOpenGmailModal={() => setIsGmailModalOpen(true)}
            />

            {/* 2. Player Profile with Level & XP */}
            <PlayerProfile stats={playerStats} />

            {/* 3. Inbox Health & Telemetry Metrics */}
            <InboxHealth />

            {/* 4. How to Play & Move List */}
            <HowToPlay />

            {/* 5. Retro Footer */}
            <ArcadeFooter />
          </div>
        ) : (
          /* Playable Battle Arena */
          <BattleArena
            playerStats={playerStats}
            setPlayerStats={setPlayerStats}
            onGoHome={() => setCurrentView('home')}
          />
        )}
      </main>

      {/* Connect Gmail Coming Soon Modal */}
      <GmailModal
        isOpen={isGmailModalOpen}
        onClose={() => setIsGmailModalOpen(false)}
        onPlayDemo={() => {
          setIsGmailModalOpen(false);
          setCurrentView('arena');
        }}
      />

    </div>
  );
};

export default App;
