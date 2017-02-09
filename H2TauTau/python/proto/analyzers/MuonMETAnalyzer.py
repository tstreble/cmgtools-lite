import ROOT

from PhysicsTools.Heppy.analyzers.core.AutoHandle import AutoHandle
from PhysicsTools.Heppy.physicsobjects.Muon import Muon
from PhysicsTools.Heppy.physicsobjects.Electron import Electron
from PhysicsTools.Heppy.physicsobjects.Tau import Tau

from CMGTools.H2TauTau.proto.analyzers.LeptonMETAnalyzer import LeptonMETAnalyzer
from CMGTools.H2TauTau.proto.physicsobjects.ObjectMET import MuonMET


class MuonMETAnalyzer(LeptonMETAnalyzer):

    """    """
    
    LeptonMETClass = MuonMET
    LeptonClass = Muon 
    LeptonVeto1Class = Electron
    LeptonVeto2Class = Tau
    
    def declareHandles(self):
        super(MuonMETAnalyzer, self).declareHandles()

        self.handles['leptons'] = AutoHandle(
            'slimmedMuons',
            'std::vector<pat::Muon>'
        )

        self.handles['leptonVeto1'] = AutoHandle(
            'slimmedElectrons',
            'std::vector<pat::Electron>'
        )

        self.handles['leptonVeto2'] = AutoHandle(
            'slimmedTaus',
            'std::vector<pat::Tau>'
        )

        self.mchandles['genParticles'] = AutoHandle(
            'prunedGenParticles',
            'std::vector<reco::GenParticle>'
        )

        self.handles['puppiMET'] = AutoHandle(
            'slimmedMETsPuppi',
            'std::vector<pat::MET>'
        )

        self.handles['pfMET'] = AutoHandle(
            'slimmedMETs',
            'std::vector<pat::MET>'
        )

    def process(self, event):
        # Take the pre-sorted vertices from miniAOD
        event.goodVertices = event.vertices

        result = super(MuonMETAnalyzer, self).process(event)

        event.pfmet = self.handles['pfMET'].product()[0]
        event.puppimet = self.handles['puppiMET'].product()[0]

        return result
    
    def buildLeptons(self, patLeptons, event):
        '''Build muons for veto, associate best vertex, select loose ID muons.
        The loose ID selection is done to ensure that the muon has an inner track.'''
        leptons = []
        for index, lep in enumerate(patLeptons):
            muon = self.__class__.LeptonClass(lep)
            muon.associatedVertex = event.goodVertices[0]
            if muon.muonID('POG_ID_Medium_ICHEP') and self.testVertex(muon):
                leptons.append(muon)
        return leptons

    def buildLeptonsVeto1(self, patLeptons, event):
        '''Build muons for veto, associate best vertex, select loose ID muons.
        The loose ID selection is done to ensure that the muon has an inner track.'''
        leptons = []
        for index, lep in enumerate(patLeptons):
            ele = self.__class__.LeptonVeto1Class(lep)
            ele.associatedVertex = event.goodVertices[0]
            leptons.append(ele)
        return leptons

    def buildLeptonsVeto2(self, patLeptons, event):
        '''Build muons for veto, associate best vertex, select loose ID muons.
        The loose ID selection is done to ensure that the muon has an inner track.'''
        leptons = []
        for index, lep in enumerate(patLeptons):
            tau = self.__class__.LeptonVeto2Class(lep)
            tau.associatedVertex = event.goodVertices[0]
            leptons.append(tau)
        return leptons

    def veto1(self, electrons):
        # count electrons
        vEles = [electron for electron in electrons if
                 electron.pt() > 10 and
                 abs(electron.eta()) < 2.5 and
                 self.testVertex(electron) and
                 electron.mvaIDRun2('NonTrigSpring15MiniAOD', 'POG90') and
                 electron.passConversionVeto() and
                 electron.physObj.gsfTrack().hitPattern().numberOfHits(ROOT.reco.HitPattern.MISSING_INNER_HITS) <= 1 and
                 electron.relIsoR(R=0.3, dBetaFactor=0.5, allCharged=0) < 0.3]
        if vEles:
            return False
        return True

    def veto2(self, taus):
        # count taus
        vTaus = [tau for tau in taus if
                 self.testTauVertex(tau) and
                 tau.tauID('decayModeFinding') and 
                 tau.tauID('byVLooseIsolationMVArun2v1DBoldDMwLT') and 
                 tau.pt() > 18. and 
                 abs(tau.eta()) < 2.5]
        if vTaus:
            return False
        return True

    def testTauVertex(self, tau):
        '''Tests vertex constraints, for tau'''
        # Just checks if the primary vertex the tau was reconstructed with
        # corresponds to the one used in the analysis
        # isPV = abs(tau.vertex().z() - tau.associatedVertex.z()) < 0.2
        isPV = abs(tau.leadChargedHadrCand().dz()) < 0.2
        return isPV

    def testVertex(self, lepton):
        '''Tests vertex constraints, for mu'''
        return abs(lepton.dxy()) < 0.045 and abs(lepton.dz()) < 0.2

    def buildLeptonMET(self, cmgLeptons, event):
        '''Creates python DiLeptons from the di-leptons read from the disk.
        to be overloaded if needed.'''
        met = self.handles['pfMET'].product()[0]
        return map(self.__class__.LeptonMETClass, cmgLeptons, [met for i in range(len(cmgLeptons))])
